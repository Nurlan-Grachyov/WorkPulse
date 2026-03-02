const API_BASE = window.location.origin;
let accessToken = null;

// восстановление токена из localStorage
(function restoreToken() {
    try {
        const saved = window.localStorage.getItem("accessToken");
        if (saved) {
            accessToken = saved;
        }
    } catch (e) {
        console.warn("Cannot access localStorage", e);
    }
})();

/* ===== Уведомления ===== */

function showNotification(message, type = "success", timeout = 3000) {
    const note = document.getElementById("notification");
    if (!note) return;
    note.className = ""; // сброс классов
    note.classList.add(type === "error" ? "error" : "success");
    note.textContent = message;
    note.style.display = "block";

    if (timeout) {
        setTimeout(() => {
            note.style.display = "none";
        }, timeout);
    }
}

function setStatus(msg, ok = true) {
    const el = document.getElementById("status");
    if (el) {
        el.textContent = msg;
        el.style.color = ok ? "green" : "red";
    }
    showNotification(msg, ok ? "success" : "error");
}

/* ===== Регистрация / Логин / Логаут ===== */

async function registerUser() {
    const emailEl = document.getElementById("reg_email");
    const passEl = document.getElementById("reg_password");
    if (!emailEl || !passEl) return;

    const email = emailEl.value;
    const password = passEl.value;
    if (!email || !password) {
        setStatus("Введите email и пароль для регистрации", false);
        return;
    }
    try {
        const resp = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok) {
            let msg =
                typeof data.detail === "string" ? data.detail : JSON.stringify(data);
            setStatus(`Ошибка регистрации: ${msg}`, false);
            return;
        }
        setStatus("Пользователь успешно зарегистрирован", true);
        emailEl.value = "";
        passEl.value = "";
    } catch (e) {
        console.error(e);
        setStatus("Сетевая ошибка при регистрации", false);
    }
}

async function login() {
    const usernameEl = document.getElementById("login_username");
    const passwordEl = document.getElementById("login_password");
    if (!usernameEl || !passwordEl) return;

    const username = usernameEl.value;
    const password = passwordEl.value;

    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const resp = await fetch(`${API_BASE}/auth/jwt/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData.toString(),
        });

        let data = {};
        try {
            data = await resp.json();
        } catch (_) {
            data = {};
        }

        if (!resp.ok) {
            let msg = "";
            if (typeof data.detail === "string") msg = data.detail;
            else if (Array.isArray(data.detail))
                msg = data.detail
                    .map(
                        (d) =>
                            `${d.msg || ""} (${
                                d.loc ? d.loc.join(".") : ""
                            })`
                    )
                    .join("; ");
            else msg = JSON.stringify(data);
            setStatus(`Ошибка логина: ${msg}`, false);
            accessToken = null;
            window.localStorage.removeItem("accessToken");
            return;
        }

        accessToken = data.access_token;
        if (!accessToken) {
            setStatus("Нет access_token в ответе", false);
            console.log("data:", data);
            return;
        }
        window.localStorage.setItem("accessToken", accessToken);
        setStatus("Успешная аутентификация", true);
    } catch (e) {
        console.error(e);
        setStatus("Сетевая ошибка при логине", false);
    }
}

function logoutUser() {
    accessToken = null;
    try {
        window.localStorage.removeItem("accessToken");
    } catch (e) {
        console.warn("Cannot access localStorage", e);
    }
    setStatus("Вы вышли из системы", true);
    // опционально: редирект на главную
    if (window.location.pathname !== "/") {
        window.location.href = "/";
    }
}

/* ===== Обёртка для запросов с токеном ===== */

async function authedFetch(path, options = {}, outputId = null, successMsg = null) {
    if (!accessToken) {
        setStatus("Сначала залогинься", false);
        return null;
    }
    const headers = {
        Authorization: `Bearer ${accessToken}`,
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
    };
    try {
        const resp = await fetch(`${API_BASE}${path}`, {
            ...options,
            headers,
        });
        const data = await resp.json().catch(() => ({}));

        if (!resp.ok) {
            let msg =
                typeof data.detail === "string" ? data.detail : JSON.stringify(data);
            setStatus(`Ошибка: ${msg}`, false);
            if (outputId) {
                const outEl = document.getElementById(outputId);
                if (outEl) outEl.textContent = "";
            }
            return null;
        }
        if (successMsg) setStatus(successMsg, true);
        if (outputId) {
            const outEl = document.getElementById(outputId);
            if (outEl)
                outEl.textContent = JSON.stringify(data, null, 2);
        }
        return data;
    } catch (e) {
        console.error(e);
        setStatus("Сетевая ошибка", false);
        if (outputId) {
            const outEl = document.getElementById(outputId);
            if (outEl) outEl.textContent = "";
        }
        return null;
    }
}

/* ===== USERS ===== */

async function loadUsers() {
    await authedFetch(
        "/users/all_users/",
        { method: "GET" },
        "users_output",
        "Список пользователей загружен"
    );
}

/* ===== TEAMS ===== */

async function createTeam() {
    const titleEl = document.getElementById("team_title");
    if (!titleEl) return;
    const title = titleEl.value;
    if (!title) return setStatus("Введите название команды", false);

    await authedFetch(
        "/team/create_team",
        {
            method: "POST",
            body: JSON.stringify({ title_team: title }),
        },
        "team_output",
        "Команда успешно создана"
    );
    titleEl.value = "";
}

async function loadTeamUsers() {
    const slugEl = document.getElementById("team_slug_users");
    if (!slugEl) return;
    const slug = slugEl.value;
    if (!slug) return setStatus("Введите slug команды", false);
    await authedFetch(
        `/team/${slug}/users/`,
        { method: "GET" },
        "team_users_output",
        "Пользователи команды загружены"
    );
}

async function addUserToTeam() {
    const slugEl = document.getElementById("add_team_slug");
    const emailEl = document.getElementById("add_user_email");
    const roleEl = document.getElementById("add_user_role");
    if (!slugEl || !emailEl || !roleEl) return;

    const slug = slugEl.value;
    const email = emailEl.value;
    const role = roleEl.value;

    if (!slug || !email)
        return setStatus("Укажи slug команды и email", false);

    const params = new URLSearchParams({ user_email: email, role });
    await authedFetch(
        `/team/${slug}/users/add_user/?${params.toString()}`,
        {
            method: "POST",
        },
        "add_team_user_output",
        "Пользователь добавлен в команду"
    );
}

/* ===== TASKS ===== */

async function createTask() {
    const titleEl = document.getElementById("task_title");
    const descrEl = document.getElementById("task_description");
    const assigneeEl = document.getElementById("task_assignee_email");
    const deadlineEl = document.getElementById("task_deadline");
    if (!titleEl || !assigneeEl) return;

    const title = titleEl.value;
    const description = descrEl ? descrEl.value : "";
    const assigneeEmail = assigneeEl.value;
    const deadline = deadlineEl ? deadlineEl.value : "";

    if (!title || !assigneeEmail)
        return setStatus("Нужны title и assignee_email", false);

    const payload = {
        title,
        description,
        assignee_email: assigneeEmail,
        deadline: deadline || null,
    };
    await authedFetch(
        "/tasks/create_task",
        {
            method: "POST",
            body: JSON.stringify(payload),
        },
        "task_output",
        "Задача успешно создана"
    );
}

async function loadTask() {
    const slugEl = document.getElementById("get_task_slug");
    if (!slugEl) return;
    const slug = slugEl.value;
    if (!slug) return setStatus("Укажи slug задачи", false);
    await authedFetch(
        `/tasks/${slug}`,
        { method: "GET" },
        "get_task_output",
        "Задача загружена"
    );
}

/* ===== EVALUATIONS ===== */

async function evaluateTask() {
    const taskIdEl = document.getElementById("eval_task_id");
    const scoreEl = document.getElementById("eval_score");
    const commentEl = document.getElementById("eval_comment");
    if (!taskIdEl || !scoreEl) return;

    const taskId = taskIdEl.value;
    const score = scoreEl.value;
    const comment = commentEl ? commentEl.value : "";

    if (!taskId || !score)
        return setStatus("Нужны task_id и оценка", false);

    const payload = {
        task_id: Number(taskId),
        evaluation: Number(score),
        comment: comment || null,
    };
    await authedFetch(
        "/evaluations/create_evaluation",
        {
            method: "POST",
            body: JSON.stringify(payload),
        },
        "eval_output",
        "Оценка сохранена"
    );
}

async function loadEvaluations() {
    await authedFetch(
        "/evaluations/get_evaluations",
        { method: "GET" },
        "evaluations_output",
        "Оценки загружены"
    );
}

/* ===== COMMENTS ===== */

async function commentTask() {
    const taskIdEl = document.getElementById("comment_task_id");
    const textEl = document.getElementById("comment_text");
    if (!taskIdEl || !textEl) return;

    const taskId = taskIdEl.value;
    const text = textEl.value;
    if (!taskId || !text)
        return setStatus("Нужны task_id и текст комментария", false);

    const payload = {
        task_id: Number(taskId),
        text: text,
    };
    await authedFetch(
        "/comments/create_comment",
        {
            method: "POST",
            body: JSON.stringify(payload),
        },
        "comment_output",
        "Комментарий добавлен"
    );
}

async function loadCommentsByTask() {
    const taskIdEl = document.getElementById("comment_task_id_get");
    if (!taskIdEl) return;
    const taskId = taskIdEl.value;
    if (!taskId) return setStatus("Нужен task_id", false);

    await authedFetch(
        `/comments/tasks/${taskId}`,
        { method: "GET" },
        "comments_task_output",
        "Комментарии загружены"
    );
}

/* ===== MEETINGS ===== */

async function createMeeting() {
    const titleEl = document.getElementById("meeting_title");
    const startsEl = document.getElementById("meeting_starts_at");
    const descrEl = document.getElementById("meeting_description");
    if (!titleEl || !startsEl) return;

    const title = titleEl.value;
    const startsAt = startsEl.value;
    const descr = descrEl ? descrEl.value : "";

    if (!title || !startsAt)
        return setStatus("Нужны title и starts_at", false);

    const payload = {
        title,
        starts_at: startsAt,
        description: descr || null,
    };
    await authedFetch(
        "/meetings/create_meeting",
        {
            method: "POST",
            body: JSON.stringify(payload),
        },
        "meeting_output",
        "Митинг успешно создан"
    );
}

async function loadMeeting() {
    const idEl = document.getElementById("get_meeting_id");
    if (!idEl) return;
    const id = idEl.value;
    if (!id) return setStatus("Нужен meeting_id", false);
    await authedFetch(
        `/meetings/${id}`,
        { method: "GET" },
        "get_meeting_output",
        "Митинг загружен"
    );
}

/* ===== CALENDAR ===== */

async function loadCalendar() {
    const periodEl = document.getElementById("calendar_period");
    if (!periodEl) return;
    const period = periodEl.value;
    await authedFetch(
        `/calendar/?period=${period}`,
        { method: "GET" },
        "calendar_output",
        "Календарь загружен"
    );
}
