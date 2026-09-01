import React, { useEffect, useState } from "react";
import * as api from "./api.js";

export default function App() {
  const [todos, setTodos] = useState([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function reload() {
    setLoading(true);
    setError("");
    try {
      setTodos(await api.fetchTodos());
    } catch (e) {
      setError(e.message || "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, []);

  async function onAdd(e) {
    e.preventDefault();
    try {
      await api.createTodo(title);
      setTitle("");
      await reload();
    } catch (err) {
      setError(err.message || "error");
    }
  }

  return (
    <main>
      <h1>Todo</h1>
      <form onSubmit={onAdd}>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="New todo" />
        <button type="submit">Add</button>
      </form>
      {loading && <p>Loading…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && todos.length === 0 && <p>No todos yet.</p>}
      <ul>
        {todos.map((t) => (
          <li key={t.id} className={t.completed ? "done" : ""}>
            <span>{t.title}</span>
            <button type="button" onClick={() => api.toggleTodo(t.id).then(reload)}>
              Toggle
            </button>
            <button type="button" onClick={() => api.deleteTodo(t.id).then(reload)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
