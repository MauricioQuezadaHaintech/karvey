import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
from karvey_lib import atomicio, EXIT_NOT_FOUND, EXIT_REFUSED


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.f = self.d / "spec.json"

    def tearDown(self):
        self.tmp.cleanup()


class Read(Base):
    def test_utf8_sig(self):
        self.f.write_bytes(b"\xef\xbb\xbf" + '{"phase": "impl", "n": "ñ"}\n'.encode())
        ld = atomicio.read_json(self.f)
        self.assertEqual(ld.data, {"phase": "impl", "n": "ñ"})
        self.assertTrue(ld.bom)

    def test_missing_and_corrupt_exit_4(self):
        with self.assertRaises(atomicio.ReadError) as cm:
            atomicio.read_json(self.d / "nope.json")
        self.assertEqual(cm.exception.exit_code, EXIT_NOT_FOUND)
        self.f.write_text("{not json")
        with self.assertRaises(atomicio.ReadError):
            atomicio.read_json(self.f)


class FormatPreservation(Base):
    def test_key_order_and_two_space_indent(self):
        src = '{\n  "zeta": 1,\n  "alpha": {\n    "b": 2,\n    "a": "é"\n  }\n}\n'
        self.f.write_text(src, encoding="utf-8")
        ld = atomicio.read_json(self.f)
        atomicio.write_json(self.f, ld.data, loaded=ld)
        self.assertEqual(self.f.read_text(encoding="utf-8"), src)

    def test_other_indent_crlf_and_bom_kept(self):
        src = "﻿{\r\n    \"b\": 1,\r\n    \"a\": 2\r\n}"
        self.f.write_bytes(src.encode("utf-8"))
        ld = atomicio.read_json(self.f)
        ld.data["c"] = 3
        atomicio.write_json(self.f, ld.data, loaded=ld)
        out = self.f.read_bytes().decode("utf-8")
        self.assertTrue(out.startswith("﻿{\r\n    \"b\": 1,"))
        self.assertFalse(out.endswith("\n"))
        self.assertEqual(list(json.loads(out[1:])), ["b", "a", "c"])

    def test_new_file_defaults_to_two_spaces(self):
        atomicio.write_json(self.f, {"b": 1, "a": 2})
        self.assertEqual(self.f.read_text(), '{\n  "b": 1,\n  "a": 2\n}\n')


class Atomic(Base):
    def test_tmp_then_os_replace_same_dir(self):
        self.f.write_text('{"a": 1}\n')
        ld = atomicio.read_json(self.f)
        calls = []
        real = os.replace

        def spy(src, dst):
            calls.append((src, dst))
            return real(src, dst)

        with mock.patch("karvey_lib.atomicio.os.replace", side_effect=spy):
            atomicio.write_json(self.f, {"a": 2}, loaded=ld)
        self.assertEqual(len(calls), 1)
        self.assertEqual(Path(calls[0][0]).parent, self.d)
        self.assertEqual(Path(calls[0][1]), self.f)
        self.assertEqual(json.loads(self.f.read_text()), {"a": 2})
        self.assertEqual(sorted(p.name for p in self.d.iterdir()), ["spec.json"])  # no tmp, no lock left

    def test_failed_replace_leaves_original(self):
        self.f.write_text('{"a": 1}\n')
        ld = atomicio.read_json(self.f)
        with mock.patch("karvey_lib.atomicio.os.replace", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                atomicio.write_json(self.f, {"a": 2}, loaded=ld)
        self.assertEqual(self.f.read_text(), '{"a": 1}\n')
        self.assertEqual(sorted(p.name for p in self.d.iterdir()), ["spec.json"])

    @unittest.skipIf(os.name == "nt", "POSIX permission bits: Windows chmod only toggles read-only (F-42)")
    def test_mode_preserved(self):
        self.f.write_text('{"a": 1}\n')
        os.chmod(self.f, 0o640)
        ld = atomicio.read_json(self.f)
        atomicio.write_json(self.f, {"a": 2}, loaded=ld)
        self.assertEqual(self.f.stat().st_mode & 0o777, 0o640)


class Lock(Base):
    def test_fresh_lock_refuses_with_exit_3(self):
        lp = Path(str(self.f) + ".lock")
        lp.write_text("123 0\n")
        with self.assertRaises(atomicio.LockBusy) as cm:
            with atomicio.lock(self.f, wait_s=0.2):
                pass
        self.assertEqual(cm.exception.exit_code, EXIT_REFUSED)
        self.assertTrue(lp.exists())  # someone else's lock is not removed

    def test_stale_after_30s_is_broken(self):
        lp = Path(str(self.f) + ".lock")
        lp.write_text("123 0\n")
        old = time.time() - 31
        os.utime(lp, (old, old))
        with atomicio.lock(self.f, wait_s=0.2):
            self.assertTrue(lp.exists())
        self.assertFalse(lp.exists())

    def test_not_stale_at_29s(self):
        lp = Path(str(self.f) + ".lock")
        lp.write_text("x")
        old = time.time() - 29
        os.utime(lp, (old, old))
        with self.assertRaises(atomicio.LockBusy):
            with atomicio.lock(self.f, wait_s=0.1):
                pass

    def test_waits_for_release(self):
        released = []

        def holder():
            with atomicio.lock(self.f):
                time.sleep(0.3)
                released.append(1)

        t = threading.Thread(target=holder)
        t.start()
        time.sleep(0.05)
        with atomicio.lock(self.f, wait_s=2):
            self.assertEqual(released, [1])
        t.join()


class CompareAndSwap(Base):
    def test_other_writer_refused_exit_3_nothing_written(self):
        self.f.write_text('{"phase": "tasks"}\n')
        ld = atomicio.read_json(self.f)
        self.f.write_text('{"phase": "impl"}\n')  # someone else
        with self.assertRaises(atomicio.CASConflict) as cm:
            atomicio.write_json(self.f, {"phase": "test"}, loaded=ld)
        self.assertEqual(cm.exception.exit_code, EXIT_REFUSED)
        self.assertEqual(self.f.read_text(), '{"phase": "impl"}\n')
        self.assertFalse(Path(str(self.f) + ".lock").exists())

    def test_create_requires_absent(self):
        atomicio.write_json(self.f, {"a": 1})  # expected None = must not exist
        with self.assertRaises(atomicio.CASConflict):
            atomicio.write_json(self.f, {"a": 2})
        atomicio.write_json(self.f, {"a": 3}, expected_sha256="*")
        self.assertEqual(json.loads(self.f.read_text()), {"a": 3})

    def test_returns_new_hash(self):
        self.f.write_text("{}\n")
        ld = atomicio.read_json(self.f)
        h = atomicio.write_json(self.f, {"a": 1}, loaded=ld)
        self.assertEqual(h, atomicio.file_sha256(self.f))


class LockOwnership(unittest.TestCase):
    """BUG-37: breaking a stale lock raced between stat and unlink (a waiter could remove the fresh lock another
    waiter had just taken, and both held it), and the release removed the lock even when it was not its own."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        self.d = tempfile.TemporaryDirectory()
        self.path = Path(self.d.name) / "spec.json"
        self.path.write_text("{}", encoding="utf-8")

    def tearDown(self):
        self.d.cleanup()

    def test_release_keeps_a_lock_that_is_not_ours(self):
        with atomicio.lock(self.path) as lp:
            lp.write_bytes(b"another owner\n")
        self.assertTrue(lp.exists())
        self.assertEqual(lp.read_bytes(), b"another owner\n")

    def test_breaking_does_not_remove_a_fresh_lock_taken_meanwhile(self):
        import os
        lp = self.path.with_name(self.path.name + ".lock")
        lp.write_bytes(b"stale\n")
        old = os.stat(lp)
        os.utime(lp, (old.st_atime - 100, old.st_mtime - 100))
        seen = os.stat(lp).st_ino
        os.rename(lp, str(lp) + ".held")  # another waiter broke it (the old inode stays alive) ...
        lp.write_bytes(b"fresh owner\n")  # ... and took a fresh lock
        self.assertFalse(atomicio._break_stale(lp, seen, 30))
        self.assertEqual(lp.read_bytes(), b"fresh owner\n")

    def test_a_stale_lock_is_still_broken(self):
        import os
        lp = self.path.with_name(self.path.name + ".lock")
        lp.write_bytes(b"stale\n")
        old = os.stat(lp)
        os.utime(lp, (old.st_atime - 100, old.st_mtime - 100))
        with atomicio.lock(self.path, wait_s=1.0):
            pass
        self.assertFalse(lp.exists())


if __name__ == "__main__":
    unittest.main()
