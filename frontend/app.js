async function loadStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();

  document.getElementById("meta").innerText =
    `Checked every ${data.checked_every_minutes} minutes | Timezone: ${data.timezone}`;

  const container = document.getElementById("cards");
  container.innerHTML = "";

  data.targets.forEach(t => {
    const div = document.createElement("div");
    div.className = `card ${t.status.toLowerCase()}`;

    div.innerHTML = `
      <div><strong>${t.name}</strong></div>
      <div>${t.url}</div>
      <div class="status">${t.status}</div>
      <div>Last downtime: ${t.last_downtime}</div>
      ${t.error ? `<div class="error">${t.error}</div>` : ""}
    `;

    container.appendChild(div);
  });
}

loadStatus();
setInterval(loadStatus, 60000);
