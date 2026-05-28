import { PRODUCT_LINKS } from "./product-links.js";

export function errorHelpUrl(code: string): string {
  return `${PRODUCT_LINKS.githubPages}errors/${encodeURIComponent(code)}/`;
}
