from datetime import date, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.app_user import AppUser
from app.models.cooperative import Cooperative
from app.models.land_plot import LandPlot
from app.models.owner import Owner
from app.models.plot_ownership import PlotOwnership


@pytest.fixture
async def admin_token(test_db) -> str:
    """Создаёт admin пользователя и возвращает токен."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    admin = AppUser(
        username="admin_user",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        is_active=True,
    )
    test_db.add(admin)
    await test_db.commit()

    return create_access_token(data={"sub": "admin_user", "role": "admin"})


@pytest.fixture
async def treasurer_token(test_db) -> str:
    """Создаёт treasurer пользователя с СТ и возвращает токен."""
    coop = Cooperative(name="СТ Казначея")
    test_db.add(coop)
    await test_db.flush()

    treasurer = AppUser(
        username="treasurer_user",
        email="treasurer@example.com",
        hashed_password=get_password_hash("treasurerpass"),
        role="treasurer",
        cooperative_id=coop.id,
        is_active=True,
    )
    test_db.add(treasurer)
    await test_db.commit()

    return create_access_token(data={"sub": "treasurer_user", "role": "treasurer"})


@pytest.fixture
async def owner_test_data(test_db) -> Owner:
    """Создаёт тестового владельца."""
    owner = Owner(
        owner_type="physical",
        name="Иванов Иван Иванович",
        tax_id="123456789",
        contact_phone="+375291234567",
        contact_email="ivanov@example.com",
    )
    test_db.add(owner)
    await test_db.commit()
    return owner


@pytest.fixture
async def second_owner_test_data(test_db) -> Owner:
    """Создаёт второго тестового владельца."""
    owner = Owner(
        owner_type="physical",
        name="Петров Пётр Петрович",
        tax_id="987654321",
    )
    test_db.add(owner)
    await test_db.commit()
    return owner


@pytest.mark.asyncio
async def test_create_land_plot_with_single_owner(
    async_client: AsyncClient,
    treasurer_token: str,
    owner_test_data: Owner,
) -> None:
    """Тест создания участка с одним владельцем."""
    # Получаем cooperative_id из токена
    coop_response = await async_client.get(
        "/api/v1/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    response = await async_client.post(
        "/api/v1/land-plots/",
        json={
            "cooperative_id": coop_id,
            "plot_number": "123",
            "area_sqm": "600.00",
            "cadastral_number": "123/456/789",
            "status": "active",
            "ownerships": [
                {
                    "owner_id": str(owner_test_data.id),
                    "share_numerator": 1,
                    "share_denominator": 1,
                    "is_primary": True,
                    "valid_from": str(date.today()),
                }
            ],
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["plot_number"] == "123"
    assert data["area_sqm"] == "600.00"
    assert "financial_subject_id" in data
    assert "financial_subject_code" in data


@pytest.mark.asyncio
async def test_create_land_plot_with_multiple_owners(
    async_client: AsyncClient,
    admin_token: str,
    owner_test_data: Owner,
    second_owner_test_data: Owner,
    test_db,
) -> None:
    """Тест создания участка с несколькими владельцами (доли 1/2, 1/2)."""
    # Создаём СТ для admin
    coop = Cooperative(name="СТ Для теста участков")
    test_db.add(coop)
    await test_db.flush()

    response = await async_client.post(
        "/api/v1/land-plots/",
        json={
            "cooperative_id": str(coop.id),
            "plot_number": "456",
            "area_sqm": "1000.00",
            "status": "active",
            "ownerships": [
                {
                    "owner_id": str(owner_test_data.id),
                    "share_numerator": 1,
                    "share_denominator": 2,
                    "is_primary": True,
                    "valid_from": str(date.today()),
                },
                {
                    "owner_id": str(second_owner_test_data.id),
                    "share_numerator": 1,
                    "share_denominator": 2,
                    "is_primary": False,
                    "valid_from": str(date.today()),
                },
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["plot_number"] == "456"
    assert data["financial_subject_id"] is not None


@pytest.mark.asyncio
async def test_get_land_plots_list(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
) -> None:
    """Тест получения списка участков."""
    # Получаем СТ казначея
    coop_response = await async_client.get(
        "/api/v1/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    # Создаём участки
    for i in range(3):
        plot = LandPlot(
            cooperative_id=UUID(coop_id),
            plot_number=f"Участок {i}",
            area_sqm="500.00",
            status="active",
        )
        test_db.add(plot)
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/land-plots/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_get_land_plot_by_id(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
) -> None:
    """Тест получения участка по ID с владельцами."""
    # Получаем СТ казначея
    coop_response = await async_client.get(
        "/api/v1/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    # Создаём участок
    plot = LandPlot(
        cooperative_id=UUID(coop_id),
        plot_number="Тестовый",
        area_sqm="700.00",
    )
    test_db.add(plot)
    await test_db.commit()

    response = await async_client.get(
        f"/api/v1/land-plots/{plot.id}",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["plot_number"] == "Тестовый"
    assert "owners" in data
    assert "financial_subject_id" in data


@pytest.mark.asyncio
async def test_get_land_plot_not_found(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест получения несуществующего участка."""
    import uuid
    fake_id = uuid.uuid4()

    response = await async_client.get(
        f"/api/v1/land-plots/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_land_plot(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
) -> None:
    """Тест обновления участка."""
    # Получаем СТ казначея
    coop_response = await async_client.get(
        "/api/v1/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    # Создаём участок
    plot = LandPlot(
        cooperative_id=UUID(coop_id),
        plot_number="До обновления",
        area_sqm="500.00",
    )
    test_db.add(plot)
    await test_db.commit()

    response = await async_client.patch(
        f"/api/v1/land-plots/{plot.id}",
        json={
            "plot_number": "После обновления",
            "status": "archived",
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["plot_number"] == "После обновления"
    assert data["status"] == "archived"


@pytest.mark.asyncio
async def test_update_land_plot_not_found(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест обновления несуществующего участка."""
    import uuid
    fake_id = uuid.uuid4()

    response = await async_client.patch(
        f"/api/v1/land-plots/{fake_id}",
        json={"plot_number": "Новый номер"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_land_plot_by_admin(
    async_client: AsyncClient,
    test_db,
    admin_token: str,
) -> None:
    """Тест удаления участка от имени admin."""
    coop = Cooperative(name="СТ На удаление")
    test_db.add(coop)
    await test_db.flush()

    plot = LandPlot(
        cooperative_id=coop.id,
        plot_number="На удаление",
        area_sqm="500.00",
    )
    test_db.add(plot)
    await test_db.commit()
    plot_id = plot.id

    response = await async_client.delete(
        f"/api/v1/land-plots/{plot_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_land_plot_by_treasurer_forbidden(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
) -> None:
    """Тест 403 при попытке treasurer удалить участок."""
    # Получаем СТ казначея
    coop_response = await async_client.get(
        "/api/v1/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    plot = LandPlot(
        cooperative_id=UUID(coop_id),
        plot_number="Тест",
        area_sqm="500.00",
    )
    test_db.add(plot)
    await test_db.commit()

    response = await async_client.delete(
        f"/api/v1/land-plots/{plot.id}",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_ownership_to_plot(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
    owner_test_data: Owner,
) -> None:
    """Тест добавления владельца к участку."""
    # Получаем СТ казначея
    coop_response = await async_client.get(
        "/api/v1/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    # Создаём участок
    plot = LandPlot(
        cooperative_id=UUID(coop_id),
        plot_number="С владельцем",
        area_sqm="800.00",
    )
    test_db.add(plot)
    await test_db.commit()

    response = await async_client.post(
        f"/api/v1/land-plots/{plot.id}/ownerships",
        json={
            "land_plot_id": str(plot.id),
            "owner_id": str(owner_test_data.id),
            "share_numerator": 1,
            "share_denominator": 1,
            "is_primary": True,
            "valid_from": str(date.today()),
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["share_numerator"] == 1
    assert data["share_denominator"] == 1
    assert data["is_primary"] is True


@pytest.mark.asyncio
async def test_close_ownership(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
    owner_test_data: Owner,
) -> None:
    """Тест закрытия права собственности (установка valid_to)."""
    # Получаем СТ казначея
    coop_response = await async_client.get(
        "/api/v1/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    # Создаём участок
    plot = LandPlot(
        cooperative_id=UUID(coop_id),
        plot_number="Тест закрытия",
        area_sqm="600.00",
    )
    test_db.add(plot)
    await test_db.flush()

    # Создаём владение
    ownership = PlotOwnership(
        land_plot_id=plot.id,
        owner_id=owner_test_data.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date.today() - timedelta(days=365),
    )
    test_db.add(ownership)
    await test_db.commit()

    # Закрываем владение
    response = await async_client.patch(
        f"/api/v1/land-plots/ownerships/{ownership.id}/close",
        params={"valid_to": str(date.today())},
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid_to"] == str(date.today())


@pytest.mark.asyncio
async def test_close_ownership_not_found(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест закрытия несуществующего права собственности."""
    import uuid
    fake_id = uuid.uuid4()

    response = await async_client.patch(
        f"/api/v1/land-plots/ownerships/{fake_id}/close",
        params={"valid_to": str(date.today())},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_land_plot_auto_creates_financial_subject(
    async_client: AsyncClient,
    test_db,
    admin_token: str,
) -> None:
    """Тест что при создании участка автоматически создаётся FinancialSubject."""
    coop = Cooperative(name="СТ Для проверки ФС")
    test_db.add(coop)
    await test_db.flush()

    response = await async_client.post(
        "/api/v1/land-plots/",
        json={
            "cooperative_id": str(coop.id),
            "plot_number": "ФС Тест",
            "area_sqm": "500.00",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["financial_subject_id"] is not None
    assert data["financial_subject_code"] is not None
    assert data["financial_subject_code"].startswith("FS-")
