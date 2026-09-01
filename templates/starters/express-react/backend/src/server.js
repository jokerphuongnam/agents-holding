import express from "express";
import cors from "cors";
import * as store from "./store.js";

const app = express();
const port = Number(process.env.PORT || 3001);
app.use(cors());
app.use(express.json());

app.get("/api/health", (_req, res) => res.json({ ok: true }));
app.get("/api/todos", (_req, res) => res.json(store.listTodos()));
app.post("/api/todos", (req, res) => {
  try {
    res.status(201).json(store.createTodo(req.body?.title));
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});
app.get("/api/todos/:id", (req, res) => {
  try {
    res.json(store.getTodo(req.params.id));
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});
app.patch("/api/todos/:id", (req, res) => {
  try {
    res.json(store.updateTodo(req.params.id, req.body || {}));
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});
app.post("/api/todos/:id/toggle", (req, res) => {
  try {
    res.json(store.toggleTodo(req.params.id));
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});
app.delete("/api/todos/:id", (req, res) => {
  try {
    store.deleteTodo(req.params.id);
    res.status(204).end();
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});

if (process.env.NODE_ENV !== "test") {
  app.listen(port, () => console.log(`Todo API on http://localhost:${port}`));
}
export default app;
