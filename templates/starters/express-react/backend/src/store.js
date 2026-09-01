import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";

const dataFile = process.env.TODO_DATA_FILE || path.join(process.cwd(), "data", "todos.json");

function ensure() {
  fs.mkdirSync(path.dirname(dataFile), { recursive: true });
  if (!fs.existsSync(dataFile)) fs.writeFileSync(dataFile, "[]");
}

export function listTodos() {
  ensure();
  return JSON.parse(fs.readFileSync(dataFile, "utf8"));
}

function save(todos) {
  ensure();
  const tmp = dataFile + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(todos, null, 2));
  fs.renameSync(tmp, dataFile);
}

export function createTodo(title) {
  const t = String(title || "").trim();
  if (!t) {
    const err = new Error("title required");
    err.status = 400;
    throw err;
  }
  const todos = listTodos();
  const todo = { id: randomUUID(), title: t, completed: false };
  todos.push(todo);
  save(todos);
  return todo;
}

export function getTodo(id) {
  const todo = listTodos().find((x) => x.id === id);
  if (!todo) {
    const err = new Error("not found");
    err.status = 404;
    throw err;
  }
  return todo;
}

export function updateTodo(id, patch) {
  const todos = listTodos();
  const i = todos.findIndex((x) => x.id === id);
  if (i < 0) {
    const err = new Error("not found");
    err.status = 404;
    throw err;
  }
  if (patch.title !== undefined) {
    const t = String(patch.title).trim();
    if (!t) {
      const err = new Error("title required");
      err.status = 400;
      throw err;
    }
    todos[i].title = t;
  }
  if (patch.completed !== undefined) todos[i].completed = Boolean(patch.completed);
  save(todos);
  return todos[i];
}

export function deleteTodo(id) {
  const todos = listTodos();
  const next = todos.filter((x) => x.id !== id);
  if (next.length === todos.length) {
    const err = new Error("not found");
    err.status = 404;
    throw err;
  }
  save(next);
}

export function toggleTodo(id) {
  const todo = getTodo(id);
  return updateTodo(id, { completed: !todo.completed });
}
