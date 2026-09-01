export async function fetchTodos() {
  const res = await fetch("/api/todos");
  if (!res.ok) throw new Error("failed to load");
  return res.json();
}

export async function createTodo(title) {
  const res = await fetch("/api/todos", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("failed to create");
  return res.json();
}

export async function toggleTodo(id) {
  const res = await fetch(`/api/todos/${id}/toggle`, { method: "POST" });
  if (!res.ok) throw new Error("failed to toggle");
  return res.json();
}

export async function deleteTodo(id) {
  const res = await fetch(`/api/todos/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("failed to delete");
}
