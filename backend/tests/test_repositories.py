from app.models import (
    AuditLog,
    BackgroundJob,
    Business,
    Contact,
    DataSource,
    Export,
    RefreshToken,
    SearchLog,
    SocialProfile,
    User,
)
from app.repositories import (
    AuditLogRepository,
    BackgroundJobRepository,
    BusinessRepository,
    ContactRepository,
    DataSourceRepository,
    ExportRepository,
    RefreshTokenRepository,
    SearchLogRepository,
    SocialProfileRepository,
    UserRepository,
)


class DummySession:
    pass


def test_repositories_are_bound_to_expected_models() -> None:
    session = DummySession()

    expected = [
        (UserRepository(session), User),
        (RefreshTokenRepository(session), RefreshToken),
        (BusinessRepository(session), Business),
        (ContactRepository(session), Contact),
        (DataSourceRepository(session), DataSource),
        (SocialProfileRepository(session), SocialProfile),
        (SearchLogRepository(session), SearchLog),
        (ExportRepository(session), Export),
        (BackgroundJobRepository(session), BackgroundJob),
        (AuditLogRepository(session), AuditLog),
    ]

    for repository, model in expected:
        assert repository.model is model

