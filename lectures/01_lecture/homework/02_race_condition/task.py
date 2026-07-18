import threading
import time


def increment_with_race(counter: list[int], times: int) -> None:
    for _ in range(times):
        value = counter[0]
        time.sleep(0.000001)
        counter[0] = value + 1


def increment_safe(
    counter: list[int], times: int, lock: threading.Lock
) -> None:
    for _ in range(times):
        with lock:
            counter[0] += 1


class InsufficientFundsError(Exception):
    pass


class BankAccount:
    def __init__(self, initial_balance: float = 0.0) -> None:
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self.balance = float(initial_balance)
        self._lock = threading.Lock()

    def deposit(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative")
        with self._lock:
            self.balance += amount

    def withdraw(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Withdrawal amount cannot be negative")
        with self._lock:
            if amount > self.balance:
                raise InsufficientFundsError("Insufficient funds")
            self.balance -= amount

    def get_balance(self) -> float:
        with self._lock:
            return float(self.balance)
