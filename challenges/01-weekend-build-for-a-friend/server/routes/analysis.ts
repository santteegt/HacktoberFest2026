// Analysis routes (T8): similar setups, run comparison, param history. T0 stub: 501 until T8 lands.
import { Hono } from "hono";
import { notImplemented } from "../http";

const r = new Hono();
r.get("/analysis/similar", notImplemented("analysis"));
r.get("/analysis/compare", notImplemented("analysis"));
r.get("/analysis/history", notImplemented("analysis"));

export default r;
