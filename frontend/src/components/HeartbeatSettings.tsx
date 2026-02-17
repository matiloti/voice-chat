import { useState, useEffect } from "react";
import type { HeartbeatConfig } from "../types";

interface HeartbeatSettingsProps {
  onClose: () => void;
}

export function HeartbeatSettings({ onClose }: HeartbeatSettingsProps) {
  const [heartbeats, setHeartbeats] = useState<HeartbeatConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/heartbeats")
      .then((r) => r.json())
      .then((data) => {
        setHeartbeats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load heartbeats:", err);
        setLoading(false);
      });
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await fetch("/api/heartbeats", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(heartbeats),
      });
    } catch (err) {
      console.error("Failed to save heartbeats:", err);
    }
    setSaving(false);
  };

  const updateHeartbeat = (index: number, updates: Partial<HeartbeatConfig>) => {
    setHeartbeats((prev) =>
      prev.map((hb, i) => (i === index ? { ...hb, ...updates } : hb))
    );
  };

  const addHeartbeat = () => {
    setHeartbeats((prev) => [
      ...prev,
      {
        id: `custom_${Date.now()}`,
        name: "New Heartbeat",
        prompt: "Enter your heartbeat prompt here...",
        interval_minutes: 30,
        enabled: true,
      },
    ]);
  };

  const removeHeartbeat = (index: number) => {
    setHeartbeats((prev) => prev.filter((_, i) => i !== index));
  };

  if (loading) {
    return <div className="heartbeat-settings"><p>Loading...</p></div>;
  }

  return (
    <div className="heartbeat-settings">
      <h2>Heartbeat Settings</h2>
      <p className="settings-description">
        Heartbeats are periodic prompts that make the assistant proactive.
        It can check in, reflect on conversations, or search for relevant info.
      </p>

      <div className="heartbeat-list">
        {heartbeats.map((hb, i) => (
          <div key={hb.id} className={`heartbeat-item ${hb.enabled ? "enabled" : "disabled"}`}>
            <div className="heartbeat-item-header">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={hb.enabled}
                  onChange={(e) => updateHeartbeat(i, { enabled: e.target.checked })}
                />
                <span className="heartbeat-name">{hb.name}</span>
              </label>
              <button
                className="remove-btn"
                onClick={() => removeHeartbeat(i)}
                title="Remove"
              >
                ×
              </button>
            </div>

            {hb.enabled && (
              <div className="heartbeat-item-body">
                <label>
                  Name:
                  <input
                    type="text"
                    value={hb.name}
                    onChange={(e) => updateHeartbeat(i, { name: e.target.value })}
                  />
                </label>
                <label>
                  Interval (minutes):
                  <input
                    type="number"
                    min={1}
                    value={hb.interval_minutes}
                    onChange={(e) =>
                      updateHeartbeat(i, { interval_minutes: parseInt(e.target.value) || 30 })
                    }
                  />
                </label>
                <label>
                  Prompt:
                  <textarea
                    value={hb.prompt}
                    onChange={(e) => updateHeartbeat(i, { prompt: e.target.value })}
                    rows={3}
                  />
                </label>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="heartbeat-actions">
        <button className="add-btn" onClick={addHeartbeat}>
          + Add Heartbeat
        </button>
        <button className="save-btn" onClick={save} disabled={saving}>
          {saving ? "Saving..." : "Save"}
        </button>
      </div>
    </div>
  );
}
