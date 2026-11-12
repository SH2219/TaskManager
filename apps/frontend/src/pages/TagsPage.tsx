import { type FormEvent, useEffect, useState } from "react";
import { createTag, deleteTag, listTags, updateTag } from "../api";
import type { Tag } from "../api/types";
import { notify } from "../lib/notify";

export default function TagsPage() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [color, setColor] = useState("#2f6f4e");
  const [description, setDescription] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  async function load() {
    setLoading(true);
    try {
      setTags(await listTags());
    } catch (err) {
      notify.fromError(err, "Failed to load tags");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await createTag({
        name: name.trim(),
        color,
        description: description.trim() || undefined,
      });
      setName("");
      setDescription("");
      notify.success("Tag added.");
      await load();
    } catch (err) {
      notify.fromError(err, "Failed to create tag");
    }
  }

  async function handleUpdate(e: FormEvent) {
    e.preventDefault();
    if (editingId == null || !editName.trim()) return;
    try {
      await updateTag(editingId, {
        name: editName.trim(),
        description: editDescription.trim() || null,
      });
      setEditingId(null);
      notify.success("Tag updated.");
      await load();
    } catch (err) {
      notify.fromError(err, "Failed to update tag");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this tag?")) return;
    try {
      await deleteTag(id);
      notify.success("Tag deleted.");
      await load();
    } catch (err) {
      notify.fromError(err, "Failed to delete tag");
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Tags</h1>
          <p className="muted">Labels you can attach to work across projects.</p>
        </div>
      </header>
      <section className="card">
        <h2>New tag</h2>
        <form className="form-stack" onSubmit={handleCreate}>
          <input
            placeholder="Tag name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <label>
            Color
            <input type="color" value={color} onChange={(e) => setColor(e.target.value)} />
          </label>
          <input
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            Add tag
          </button>
        </form>
      </section>
      <section className="card">
        <h2>All tags</h2>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : tags.length === 0 ? (
          <p className="muted">No tags yet.</p>
        ) : (
          <ul className="list">
            {tags.map((tag) => (
              <li key={tag.id} className="list-item">
                {editingId === tag.id ? (
                  <form className="form-stack list-item-main" onSubmit={handleUpdate}>
                    <input value={editName} onChange={(e) => setEditName(e.target.value)} required />
                    <input
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      placeholder="Description"
                    />
                    <div className="form-row">
                      <button type="submit" className="btn btn-primary btn-sm">
                        Save
                      </button>
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditingId(null)}>
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <>
                    <div className="list-item-main">
                      <p className="list-title">
                        <span className="tag-swatch" style={{ background: tag.color || "#2f6f4e" }} />
                        {tag.name}
                      </p>
                      {tag.description && <p className="muted">{tag.description}</p>}
                    </div>
                    <div className="form-row">
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => {
                          setEditingId(tag.id);
                          setEditName(tag.name);
                          setEditDescription(tag.description ?? "");
                        }}
                      >
                        Edit
                      </button>
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => handleDelete(tag.id)}>
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
