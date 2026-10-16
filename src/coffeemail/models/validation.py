from pydantic import BaseModel, ConfigDict, Field


class EmailValidationResult(BaseModel):
    email: str
    format_valid: bool = Field(alias="formatValid")
    mx_valid: bool = Field(alias="mxValid")
    is_disposable: bool = Field(alias="isDisposable")
    reason: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ValidationCredits(BaseModel):
    limit: int | None = None
    used: int = 0
    remaining: int | None = None

    @property
    def unlimited(self) -> bool:
        return self.limit is None


class ValidateEmailsResponse(BaseModel):
    items: list[EmailValidationResult] = Field(default_factory=list)
    valid_count: int = Field(default=0, alias="validCount")
    invalid_count: int = Field(default=0, alias="invalidCount")
    credits: ValidationCredits = Field(default_factory=ValidationCredits)

    model_config = ConfigDict(populate_by_name=True)
