import { SERVER_URL } from "./config";

async function request(path, options = {}) {
  const res = await fetch(`${SERVER_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let data = null;
  try {
    data = await res.json();
  } catch (e) {
    data = null;
  }
  if (!res.ok) {
    const msg = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

export const api = {
  info: () => request("/api/info"),
  // Toggle: signs in if out, out if in.
  check: (studentId) =>
    request("/api/check", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId }),
    }),
  checkIn: (studentId) =>
    request("/api/check/in", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId }),
    }),
  checkOut: (studentId) =>
    request("/api/check/out", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId }),
    }),
  status: (studentId) => request(`/api/student/${encodeURIComponent(studentId)}/status`),
};
