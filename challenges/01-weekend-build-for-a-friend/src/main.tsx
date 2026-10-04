// UI entry (T4a). No service worker: this is a localhost app.
import { render } from "preact";
import { App } from "./ui/app/App";
import "./style.css";

render(<App />, document.getElementById("app")!);
