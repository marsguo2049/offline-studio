"""A process-held lock; stale lock files are harmless after process exit."""
from __future__ import annotations

import os
from pathlib import Path


class DataDirectoryLock:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.stream = (directory / '.studio.lock').open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                if self.stream.seek(0, 2) == 0:
                    self.stream.write(b'0')
                    self.stream.flush()
                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.stream.close()
            raise OSError('This data directory is already used by another Offline Studio instance.') from exc

    def close(self) -> None:
        # Closing the handle releases the OS lock. Never unlink the lock file:
        # unlinking it would allow another process to lock a different inode.
        self.stream.close()
