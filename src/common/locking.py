"""Khóa thư mục output để hai tiến trình không cùng ghi vào một run.

Vì sao cần: runner ghi từng prediction vào `predictions.jsonl` và hỗ trợ chạy
tiếp (resume). Nếu hai lệnh cùng chạy vào một thư mục, file sẽ bị trộn lẫn.

Bản cũ dùng `fcntl` (chỉ có trên Linux/macOS) nên không chạy được trên Windows.
Module này chọn cơ chế khóa theo hệ điều hành:
- Linux/macOS: `fcntl.flock`.
- Windows: `msvcrt.locking`.
Cả hai đều tự nhả khóa khi tiến trình kết thúc, kể cả khi bị tắt ngang.
"""

from contextlib import contextmanager
from pathlib import Path


@contextmanager
def directory_lock(output_dir):
    """Giữ khóa độc quyền trên `<output_dir>/.run.lock` trong khối `with`.

    Ném ValueError nếu đã có tiến trình khác giữ khóa.
    """
    path = Path(output_dir) / ".run.lock"
    with path.open("a+") as stream:
        try:
            import fcntl  # Linux/macOS
        except ImportError:
            fcntl = None
        if fcntl is not None:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("another runner is using this output directory") from exc
            yield
            return
        import msvcrt  # Windows
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise ValueError("another runner is using this output directory") from exc
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
