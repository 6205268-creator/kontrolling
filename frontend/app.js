(function () {
    "use strict";

    const API_BASE = "http://localhost:8001/api";
    const state = {
        users: [],
        selectedUserId: null,
        currentUser: null,
        snts: [],
        selectedSntId: null,
        physicalPersons: [],
        members: [],
        plots: [],
        meters: [],
        loading: false,
        error: null,
    };

    const themeToggle = document.getElementById("themeToggle");
    const userSelect = document.getElementById("userSelect");
    const sntSelect = document.getElementById("sntSelect");
    const navItems = document.querySelectorAll(".nav-item");
    const pageTitle = document.getElementById("pageTitle");
    const content = document.getElementById("content");
    const personModal = document.getElementById("personModal");
    const modalTitle = document.getElementById("modalTitle");
    const modalBody = document.getElementById("modalBody");
    const modalClose = document.getElementById("modalClose");

    const titles = {
        "dashboard": "Обзор",
        "snts": "СНТ",
        "physical-persons": "Физ. лица",
        "snt-members": "Члены СНТ",
        "plots": "Участки",
        "meters": "Счётчики",
    };

    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "dark") document.documentElement.setAttribute("data-theme", "dark");

    themeToggle.addEventListener("click", function () {
        const cur = document.documentElement.getAttribute("data-theme");
        const next = cur === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("theme", next);
    });

    function formatDate(s) {
        if (!s) return "—";
        const d = new Date(s);
        return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
    }

    function apiHeaders() {
        const h = { "Content-Type": "application/json" };
        if (state.selectedUserId != null) h["X-User-Id"] = String(state.selectedUserId);
        return h;
    }

    async function api(path) {
        const r = await fetch(API_BASE + path, { headers: apiHeaders() });
        if (!r.ok) throw new Error(await r.text().catch(function () { return r.statusText; }));
        return r.json();
    }

    function meterTypeLabel(t) {
        if (t === "electricity") return "Электричество";
        if (t === "water") return "Вода";
        return t;
    }

    async function loadUsers() {
        try {
            state.users = await fetch(API_BASE + "/users").then(function (r) { return r.json(); });
        } catch (e) {
            state.users = [];
        }
    }

    async function loadMe() {
        state.currentUser = null;
        if (state.selectedUserId == null) return;
        try {
            state.currentUser = await api("/me");
        } catch (e) {
            state.currentUser = null;
        }
    }

    async function loadSnts() {
        state.error = null;
        state.loading = true;
        try {
            state.snts = await api("/snts");
            if (state.users.length) {
                userSelect.innerHTML = "<option value=\"\">— Пользователь —</option>" +
                    state.users.map(function (u) {
                        return "<option value=\"" + u.id + "\">" + escapeHtml(u.name) + "</option>";
                    }).join("");
                if (state.selectedUserId != null) userSelect.value = String(state.selectedUserId);
            }

            if (state.currentUser && state.currentUser.role === "snt_user" && state.currentUser.snt_id != null) {
                sntSelect.classList.add("hidden");
                state.selectedSntId = state.currentUser.snt_id;
            } else {
                sntSelect.classList.remove("hidden");
                sntSelect.innerHTML = "<option value=\"\">— Выберите СНТ —</option>" +
                    state.snts.map(function (s) {
                        return "<option value=\"" + s.id + "\">" + escapeHtml(s.name) + "</option>";
                    }).join("");
                if (state.snts.length && state.selectedSntId == null) state.selectedSntId = state.snts[0].id;
                if (state.selectedSntId != null) sntSelect.value = String(state.selectedSntId);
            }
            if (state.selectedSntId != null) {
                await Promise.all([
                    loadMembers(state.selectedSntId),
                    loadPlots(state.selectedSntId),
                    loadMeters(state.selectedSntId),
                ]);
            } else {
                state.members = [];
                state.plots = [];
                state.meters = [];
            }
        } catch (e) {
            state.error = e.message;
        } finally {
            state.loading = false;
        }
    }

    async function loadPhysicalPersons() {
        state.error = null;
        state.loading = true;
        try {
            state.physicalPersons = await api("/physical-persons");
        } catch (e) {
            state.error = e.message;
        } finally {
            state.loading = false;
        }
    }

    async function loadMembers(sntId) {
        if (sntId == null) { state.members = []; return; }
        try {
            state.members = await api("/snt-members?snt_id=" + encodeURIComponent(sntId));
        } catch (e) {
            state.members = [];
        }
    }

    async function loadPlots(sntId) {
        if (sntId == null) { state.plots = []; return; }
        try {
            state.plots = await api("/plots?snt_id=" + encodeURIComponent(sntId));
        } catch (e) {
            state.plots = [];
        }
    }

    async function loadMeters(sntId) {
        if (sntId == null) { state.meters = []; return; }
        try {
            state.meters = await api("/meters?snt_id=" + encodeURIComponent(sntId));
        } catch (e) {
            state.meters = [];
        }
    }

    function escapeHtml(s) {
        if (s == null) return "";
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
    }

    userSelect.addEventListener("change", async function () {
        const v = userSelect.value;
        state.selectedUserId = v ? parseInt(v, 10) : null;
        localStorage.setItem("userId", state.selectedUserId != null ? String(state.selectedUserId) : "");
        await loadMe();
        state.selectedSntId = null;
        if (state.currentUser && state.currentUser.role === "snt_user" && state.currentUser.snt_id != null) {
            state.selectedSntId = state.currentUser.snt_id;
        }
        await loadSnts();
        await loadPhysicalPersons();
        if (state.selectedSntId != null) {
            await Promise.all([
                loadMembers(state.selectedSntId),
                loadPlots(state.selectedSntId),
                loadMeters(state.selectedSntId),
            ]);
        }
        renderSection(currentSection);
    });

    sntSelect.addEventListener("change", async function () {
        const v = sntSelect.value;
        state.selectedSntId = v ? parseInt(v, 10) : null;
        if (state.selectedSntId != null) {
            await Promise.all([
                loadMembers(state.selectedSntId),
                loadPlots(state.selectedSntId),
                loadMeters(state.selectedSntId),
            ]);
        } else {
            state.members = [];
            state.plots = [];
            state.meters = [];
        }
        renderSection(currentSection);
    });

    let currentSection = "dashboard";

    navItems.forEach(function (item) {
        item.addEventListener("click", function () {
            navItems.forEach(function (i) { i.classList.remove("active"); });
            item.classList.add("active");
            currentSection = item.dataset.section;
            pageTitle.textContent = titles[currentSection] || "";
            renderSection(currentSection);
        });
    });

    function renderSection(section) {
        if (state.error && (section !== "dashboard" || !state.snts.length)) {
            content.innerHTML = "<div class=\"err-msg\">Ошибка загрузки: " + escapeHtml(state.error) + "</div>";
            return;
        }
        switch (section) {
            case "dashboard":
                renderDashboard();
                break;
            case "snts":
                renderSnts();
                break;
            case "physical-persons":
                renderPhysicalPersons();
                break;
            case "snt-members":
                renderSntMembers();
                break;
            case "plots":
                renderPlots();
                break;
            case "meters":
                renderMeters();
                break;
            default:
                content.innerHTML = "";
        }
    }

    function renderDashboard() {
        const membersCount = state.members.length;
        const plotsCount = state.plots.length;
        const personsCount = state.physicalPersons.length;
        const metersCount = state.meters.length;
        const sntName = state.selectedSntId != null
            ? (state.snts.find(function (s) { return s.id === state.selectedSntId; }) || {}).name
            : "";

        content.innerHTML =
            "<div class=\"stats-grid\">" +
            "  <div class=\"stat-card\"><div class=\"stat-label\">Физ. лиц</div><div class=\"stat-value\">" + personsCount + "</div></div>" +
            "  <div class=\"stat-card\"><div class=\"stat-label\">СНТ</div><div class=\"stat-value\">" + state.snts.length + "</div></div>" +
            (state.selectedSntId != null
                ? ("  <div class=\"stat-card\"><div class=\"stat-label\">Членов в «" + escapeHtml(sntName) + "»</div><div class=\"stat-value\">" + membersCount + "</div></div>" +
                   "  <div class=\"stat-card\"><div class=\"stat-label\">Участков в «" + escapeHtml(sntName) + "»</div><div class=\"stat-value\">" + plotsCount + "</div></div>" +
                   "  <div class=\"stat-card\"><div class=\"stat-label\">Счётчиков в «" + escapeHtml(sntName) + "»</div><div class=\"stat-value\">" + metersCount + "</div></div>")
                : "  <div class=\"stat-card\"><div class=\"stat-label\">Выберите СНТ</div><div class=\"stat-value\">—</div></div>") +
            "</div>" +
            (state.error ? "<div class=\"err-msg\">" + escapeHtml(state.error) + "</div>" : "");
    }

    function renderSnts() {
        const rows = state.snts.map(function (s) {
            return "<tr><td>" + escapeHtml(s.name) + "</td><td>" + s.id + "</td></tr>";
        }).join("");
        content.innerHTML =
            "<div class=\"table-card\">" +
            "  <div class=\"table-header\"><h3 class=\"table-title\">Список СНТ</h3></div>" +
            "  <table><thead><tr><th>Название</th><th>ID</th></tr></thead><tbody>" +
            (rows || "<tr><td colspan=\"2\" class=\"empty-state\">Нет данных</td></tr>") +
            "</tbody></table></div>";
    }

    function renderPhysicalPersons() {
        const rows = state.physicalPersons.map(function (p) {
            return "<tr class=\"row-clickable\" data-id=\"" + p.id + "\">" +
                "<td>" + escapeHtml(p.full_name) + "</td>" +
                "<td>" + escapeHtml(p.phone || "—") + "</td>" +
                "<td>" + escapeHtml(p.inn || "—") + "</td>" +
                "</tr>";
        }).join("");
        content.innerHTML =
            "<div class=\"table-card\">" +
            "  <div class=\"table-header\"><h3 class=\"table-title\">Физ. лица</h3></div>" +
            "  <table><thead><tr><th>ФИО</th><th>Телефон</th><th>ИНН</th></tr></thead><tbody>" +
            (rows || "<tr><td colspan=\"3\" class=\"empty-state\">Нет данных</td></tr>") +
            "</tbody></table></div>";

        content.querySelectorAll("tr.row-clickable").forEach(function (row) {
            row.addEventListener("click", function () {
                openPersonModal(parseInt(row.dataset.id, 10));
            });
        });
    }

    function renderSntMembers() {
        if (state.selectedSntId == null) {
            content.innerHTML = "<div class=\"empty-state\">Выберите СНТ в шапке</div>";
            return;
        }
        const rows = state.members.map(function (m) {
            return "<tr>" +
                "<td>" + escapeHtml(m.physical_person_name || "") + "</td>" +
                "<td>" + formatDate(m.date_from) + "</td>" +
                "<td>" + (m.date_to ? formatDate(m.date_to) : "—") + "</td>" +
                "</tr>";
        }).join("");
        content.innerHTML =
            "<div class=\"table-card\">" +
            "  <div class=\"table-header\"><h3 class=\"table-title\">Члены СНТ</h3></div>" +
            "  <table><thead><tr><th>Физ. лицо</th><th>С</th><th>По</th></tr></thead><tbody>" +
            (rows || "<tr><td colspan=\"3\" class=\"empty-state\">Нет данных</td></tr>") +
            "</tbody></table></div>";
    }

    function renderPlots() {
        if (state.selectedSntId == null) {
            content.innerHTML = "<div class=\"empty-state\">Выберите СНТ в шапке</div>";
            return;
        }
        const rows = state.plots.map(function (p) {
            return "<tr><td>№" + escapeHtml(p.number) + "</td><td>" + escapeHtml(p.snt_name || "") + "</td></tr>";
        }).join("");
        content.innerHTML =
            "<div class=\"table-card\">" +
            "  <div class=\"table-header\"><h3 class=\"table-title\">Участки</h3></div>" +
            "  <table><thead><tr><th>Номер</th><th>СНТ</th></tr></thead><tbody>" +
            (rows || "<tr><td colspan=\"2\" class=\"empty-state\">Нет данных</td></tr>") +
            "</tbody></table></div>";
    }

    function renderMeters() {
        if (state.selectedSntId == null) {
            content.innerHTML = "<div class=\"empty-state\">Выберите СНТ в шапке</div>";
            return;
        }
        const rows = state.meters.map(function (m) {
            return "<tr>" +
                "<td>№" + escapeHtml(m.plot_number || "") + "</td>" +
                "<td>" + escapeHtml(m.snt_name || "") + "</td>" +
                "<td>" + escapeHtml(meterTypeLabel(m.meter_type)) + "</td>" +
                "<td>" + escapeHtml(m.serial_number || "—") + "</td>" +
                "</tr>";
        }).join("");
        content.innerHTML =
            "<div class=\"table-card\">" +
            "  <div class=\"table-header\"><h3 class=\"table-title\">Счётчики</h3></div>" +
            "  <table><thead><tr><th>Участок</th><th>СНТ</th><th>Тип</th><th>№ счётчика</th></tr></thead><tbody>" +
            (rows || "<tr><td colspan=\"4\" class=\"empty-state\">Нет данных</td></tr>") +
            "</tbody></table></div>";
    }

    async function openPersonModal(id) {
        modalTitle.textContent = "Загрузка…";
        modalBody.innerHTML = "";
        personModal.hidden = false;
        try {
            const p = await api("/physical-persons/" + id);
            modalTitle.textContent = p.full_name;
            let html = "";
            if (p.phone || p.inn) {
                html += "<div class=\"detail-block\">";
                if (p.phone) html += "<div class=\"detail-label\">Телефон</div><div class=\"detail-value\">" + escapeHtml(p.phone) + "</div>";
                if (p.inn) html += "<div class=\"detail-label\">ИНН</div><div class=\"detail-value\">" + escapeHtml(p.inn) + "</div>";
                html += "</div>";
            }
            if (p.members && p.members.length) {
                html += "<div class=\"detail-block\"><div class=\"detail-label\">Членства</div><ul class=\"detail-list\">";
                p.members.forEach(function (m) {
                    html += "<li><span>" + escapeHtml(m.snt_name || "") + "</span><span class=\"muted\">" +
                        formatDate(m.date_from) + " — " + (m.date_to ? formatDate(m.date_to) : "н.в.") + "</span></li>";
                });
                html += "</ul></div>";
            }
            if (p.plot_owners && p.plot_owners.length) {
                html += "<div class=\"detail-block\"><div class=\"detail-label\">Участки</div><ul class=\"detail-list\">";
                p.plot_owners.forEach(function (o) {
                    html += "<li><span>№" + escapeHtml(o.plot_number || "") + " (" + escapeHtml(o.snt_name || "") + ")</span><span class=\"muted\">" +
                        formatDate(o.date_from) + " — " + (o.date_to ? formatDate(o.date_to) : "н.в.") + "</span></li>";
                });
                html += "</ul></div>";
            }
            if (!html) html = "<div class=\"detail-block\"><div class=\"detail-value\">Нет связей</div></div>";
            modalBody.innerHTML = html;
        } catch (e) {
            modalBody.innerHTML = "<div class=\"err-msg\">" + escapeHtml(e.message) + "</div>";
        }
    }

    modalClose.addEventListener("click", function () {
        personModal.hidden = true;
    });
    personModal.addEventListener("click", function (e) {
        if (e.target === personModal) personModal.hidden = true;
    });

    (async function init() {
        content.innerHTML = "<div class=\"loading\">Загрузка…</div>";
        await loadUsers();
        const saved = localStorage.getItem("userId");
        if (saved) {
            const n = parseInt(saved, 10);
            if (!isNaN(n) && state.users.some(function (u) { return u.id === n; })) {
                state.selectedUserId = n;
            }
        }
        if (state.selectedUserId == null && state.users.length) {
            state.selectedUserId = state.users[0].id;
            localStorage.setItem("userId", String(state.selectedUserId));
        }
        await loadMe();
        if (state.currentUser && state.currentUser.role === "snt_user" && state.currentUser.snt_id != null) {
            state.selectedSntId = state.currentUser.snt_id;
        }
        await loadSnts();
        await loadPhysicalPersons();
        if (state.selectedSntId != null) {
            await Promise.all([
                loadMembers(state.selectedSntId),
                loadPlots(state.selectedSntId),
                loadMeters(state.selectedSntId),
            ]);
        }
        currentSection = "dashboard";
        pageTitle.textContent = titles.dashboard;
        renderDashboard();
    })();
})();
