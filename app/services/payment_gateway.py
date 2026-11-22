from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PaymentGatewayResult:
    success: bool
    transaction_reference: Optional[str] = None
    failure_reason: Optional[str] = None


class PaymentGateway(ABC):
    @abstractmethod
    async def charge(
        self, *, amount: Decimal, card_number: str, reference: str
    ) -> PaymentGatewayResult:
        raise NotImplementedError


class FakePaymentGateway(PaymentGateway):

    async def charge(
        self, *, amount: Decimal, card_number: str, reference: str
    ) -> PaymentGatewayResult:
        digits = card_number.replace(" ", "")
        if not digits.isascii() or not digits.isdigit() or not 12 <= len(digits) <= 19:
            return PaymentGatewayResult(
                success=False,
                failure_reason="Invalid test card number; expected 12 to 19 digits.",
            )

        if digits.endswith(("0002", "9999")):
            return PaymentGatewayResult(
                success=False,
                failure_reason="The test card was declined.",
            )

        if digits.endswith(("0000", "4242")):
            return PaymentGatewayResult(
                success=True,
                transaction_reference=f"fake-{reference}",
            )

        return PaymentGatewayResult(
            success=False,
            failure_reason="Unknown test card number.",
        )


def get_payment_gateway() -> PaymentGateway:
    return FakePaymentGateway()
