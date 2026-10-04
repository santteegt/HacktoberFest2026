import { registerSW } from "virtual:pwa-register";
import "./style.css";

registerSW({ immediate: true });

const net = document.getElementById("net")!;
function renderNet() {
  net.textContent = navigator.onLine ? "online" : "offline";
  net.dataset.state = navigator.onLine ? "online" : "offline";
}
addEventListener("online", renderNet);
addEventListener("offline", renderNet);
renderNet();

const tabs = document.querySelectorAll<HTMLButtonElement>("[role=tab]");
tabs.forEach((tab) =>
  tab.addEventListener("click", () => {
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      document.getElementById(`tab-${t.dataset.tab}`)!.hidden = !on;
    });
  }),
);
