const status = document.getElementById("status");

async function login(event) {
  event.preventDefault();
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  try {
    const response = await fetch("/api/login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) throw new Error("Credenciales inválidas o error en el servidor");
    const data = await response.json();
    sessionStorage.setItem("token", data.access);
    sessionStorage.setItem("refresh", data.refresh);
    status.textContent = "Inicio de sesión exitoso. Token guardado en sessionStorage.";
  } catch (error) {
    status.textContent = `Error al iniciar sesión: ${error.message}`;
  }
}

async function loadMe() {
  const token = sessionStorage.getItem("token");
  if (!token) { status.textContent = "Inicia sesión primero."; return; }
  const response = await fetch("/api/me/", { headers: { Authorization: `Bearer ${token}` } });
  status.textContent = response.ok ? JSON.stringify(await response.json(), null, 2) : `Error ${response.status}`;
}

async function loadUsers() {
  const token = sessionStorage.getItem("token");
  if (!token) { status.textContent = "Inicia sesión primero."; return; }
  const response = await fetch("/api/users/", { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) { status.textContent = `Error ${response.status}: se requiere una sesión válida y rol ADMIN.`; return; }
  const users = await response.json();
  document.getElementById("userList").replaceChildren(...users.map((user) => {
    const item = document.createElement("li");
    item.textContent = user.username;
    return item;
  }));
  status.textContent = "Usuarios cargados.";
}

document.getElementById("loginForm").addEventListener("submit", login);
document.getElementById("loadMe").addEventListener("click", loadMe);
document.getElementById("loadUsers").addEventListener("click", loadUsers);
document.getElementById("logout").addEventListener("click", () => {
  sessionStorage.removeItem("token");
  sessionStorage.removeItem("refresh");
  document.getElementById("userList").replaceChildren();
  status.textContent = "Sesión cerrada.";
});
