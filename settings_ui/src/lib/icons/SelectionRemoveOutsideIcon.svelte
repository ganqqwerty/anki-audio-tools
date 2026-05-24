<script lang="ts">
  const {
    size = 14,
    strokeWidth = 2,
  }: {
    size?: number;
    strokeWidth?: number;
  } = $props();

  const iconUid = Math.random().toString(36).slice(2, 10);
  const patternId = `aqe-selection-outside-${iconUid}`;
</script>

<svg
  xmlns="http://www.w3.org/2000/svg"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width={strokeWidth}
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"
>
  <defs>
    <pattern
      id={patternId}
      patternUnits="userSpaceOnUse"
      width="4"
      height="4"
      patternTransform="rotate(45)"
    >
      <line x1="0" y1="0" x2="0" y2="4" stroke="currentColor" stroke-width="1.35" />
    </pattern>
  </defs>
  <rect x="3" y="3" width="6" height="18" fill="currentColor" fill-opacity="0.2" stroke="none" />
  <rect x="15" y="3" width="6" height="18" fill="currentColor" fill-opacity="0.2" stroke="none" />
  <rect x="3" y="3" width="6" height="18" fill={`url(#${patternId})`} stroke="none" />
  <rect x="15" y="3" width="6" height="18" fill={`url(#${patternId})`} stroke="none" />
  <rect width="18" height="18" x="3" y="3" rx="2" />
  <path d="M9 3v18" />
  <path d="M15 3v18" />
</svg>
