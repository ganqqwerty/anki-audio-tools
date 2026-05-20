import { mount } from "svelte";
import BatchApp from "./BatchApp.svelte";

const app = mount(BatchApp, {
  target: document.getElementById("app")!,
});

export default app;
