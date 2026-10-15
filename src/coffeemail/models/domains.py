from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DomainStatus = Literal["pending", "verified", "failed"]
DomainStatusReason = Literal["dns_records_missing", "provider_pending", "provider_failed"]
DnsResolution = Literal["found", "absent", "unknown"]
DomainCheckName = Literal["spf", "dkim", "dmarc", "ownership", "infrastructureSpf"]
DomainHealthStatus = Literal["healthy", "warning", "critical"]
WarmupStatus = Literal["warming", "completed"]


class DnsRecord(BaseModel):
    """Registro que deve ser publicado no DNS do domínio."""

    type: Literal["TXT", "CNAME"] | str
    host: str
    value: str
    ttl: int | None = None
    is_infrastructure: bool = Field(default=False, alias="isInfrastructure")

    model_config = ConfigDict(populate_by_name=True)


class SendingIdentity(BaseModel):
    provider: Literal["aws_ses", "none"] | str
    state: Literal["not_provisioned", "pending", "ready", "failed"] | str
    last_synced_at: str | None = Field(default=None, alias="lastSyncedAt")

    model_config = ConfigDict(populate_by_name=True)


class DomainDnsCheck(BaseModel):
    ok: bool
    resolution: DnsResolution | str | None = None
    expected: str | None = None
    got: str | None = None
    matches: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class DkimRotation(BaseModel):
    """Rotação de DKIM pendente: a chave em uso só muda quando o TXT do novo seletor propagar."""

    domain_id: str = Field(alias="domainId")
    selector: str
    started_at: str = Field(alias="startedAt")
    record: DnsRecord

    model_config = ConfigDict(populate_by_name=True)


class CustomHostStatus(BaseModel):
    """Host próprio (return-path ou tracking) que aponta, via CNAME, para a plataforma."""

    host: str
    target: str
    verified: bool = False
    verified_at: str | None = Field(default=None, alias="verifiedAt")
    record: DnsRecord

    model_config = ConfigDict(populate_by_name=True)


class DomainDetail(BaseModel):
    """Domínio. ``checks`` e ``required_checks`` só vêm na resposta de ``verify``."""

    id: str
    name: str
    status: DomainStatus | str
    status_reason: DomainStatusReason | str | None = Field(default=None, alias="statusReason")
    sending_identity: SendingIdentity | None = Field(default=None, alias="sendingIdentity")
    dkim_selector: str | None = Field(default=None, alias="dkimSelector")
    dkim_public_key: str | None = Field(default=None, alias="dkimPublicKey")
    verified_at: str | None = Field(default=None, alias="verifiedAt")
    last_check_at: str | None = Field(default=None, alias="lastCheckAt")
    checks: dict[str, DomainDnsCheck] | None = None
    required_checks: list[DomainCheckName | str] = Field(
        default_factory=list, alias="requiredChecks"
    )
    dns_records_to_publish: list[DnsRecord] = Field(
        default_factory=list, alias="dnsRecordsToPublish"
    )
    created_at: str | None = Field(default=None, alias="createdAt")
    dkim_rotation: DkimRotation | None = Field(default=None, alias="dkimRotation")
    return_path: CustomHostStatus | None = Field(default=None, alias="returnPath")
    tracking_domain: CustomHostStatus | None = Field(default=None, alias="trackingDomain")
    tracking_domains_available: bool = Field(default=False, alias="trackingDomainsAvailable")

    model_config = ConfigDict(populate_by_name=True)


class CreateDomainResponse(BaseModel):
    id: str
    name: str
    status: DomainStatus | str
    dkim_records_to_publish: list[DnsRecord] = Field(
        default_factory=list, alias="dkimRecordsToPublish"
    )
    created_at: str | None = Field(default=None, alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ListDomainsResponse(BaseModel):
    domains: list[DomainDetail] = Field(default_factory=list)


class HealthCheck(BaseModel):
    ok: bool
    expected: str | None = None
    got: str | None = None


class DomainHealthResponse(BaseModel):
    domain_id: str = Field(alias="domainId")
    domain: str
    status: DomainHealthStatus | str
    spf: HealthCheck
    dkim: HealthCheck
    dmarc: HealthCheck
    checked_at: str = Field(alias="checkedAt")

    model_config = ConfigDict(populate_by_name=True)


class DomainWarmupStatus(BaseModel):
    """Aquecimento do domínio. ``status`` é ``completed`` quando a rampa terminou."""

    domain_id: str = Field(alias="domainId")
    status: WarmupStatus | str | None = None
    total_days: int | None = Field(default=None, alias="totalDays")
    started_at: str | None = Field(default=None, alias="startedAt")
    completed_at: str | None = Field(default=None, alias="completedAt")
    current_day: int = Field(default=0, alias="currentDay")
    daily_quota: int = Field(default=0, alias="dailyQuota")
    sent_today: int = Field(default=0, alias="sentToday")
    remaining_today: int = Field(default=0, alias="remainingToday")
    quota_used_percent: int = Field(default=0, alias="quotaUsedPercent")
    last_send_date: str | None = Field(default=None, alias="lastSendDate")

    model_config = ConfigDict(populate_by_name=True)
