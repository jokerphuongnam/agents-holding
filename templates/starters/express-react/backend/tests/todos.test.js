import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

test("store create list toggle delete and validation", async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "todo-"));
  process.env.TODO_DATA_FILE = path.join(dir, "todos.json");
  const store = await import("../src/store.js?" + Date.now());
  assert.deepEqual(store.listTodos(), []);
  const t = store.createTodo("Ship");
  assert.equal(t.title, "Ship");
  assert.equal(store.listTodos().length, 1);
  const toggled = store.toggleTodo(t.id);
  assert.equal(toggled.completed, true);
  assert.throws(() => store.createTodo(" "), (e) => e.status === 400);
  assert.throws(() => store.getTodo("missing"), (e) => e.status === 404);
  store.deleteTodo(t.id);
  assert.deepEqual(store.listTodos(), []);
  fs.rmSync(dir, { recursive: true, force: true });
});
