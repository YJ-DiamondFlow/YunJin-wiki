<script setup>
// 轻量内联图标组件
defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 }
})

const PATHS = {
  home: 'M3 11.5 12 4l9 7.5M5.5 9.8V19a1 1 0 0 0 1 1H10v-5h4v5h3.5a1 1 0 0 0 1-1V9.8',
  users: 'M8.5 11a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4Zm7.5 0a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM2.5 19.5c0-3 2.7-5 6-5s6 2 6 5M16 14.6c2.7.3 4.5 2 4.5 4.9',
  info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-13.2h.01M11 12h1v5h1',
  check: 'M9 11.5l2 2 4-4.5M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z',
  clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-13.5V12l3 2',
  book: 'M4 5.5A2.5 2.5 0 0 1 6.5 3H19v15H6.5A2.5 2.5 0 0 0 4 20.5Zm0 0V20.5M8 7.5h7',
  quote: 'M7.5 6.5C5.5 7.5 4.5 9.3 4.5 12v5.5h5V12h-3c0-2 .8-3.3 2.4-4ZM16.5 6.5c-2 1-3 2.8-3 5.5v5.5h5V12h-3c0-2 .8-3.3 2.4-4Z',
  sun: 'M12 4V2.5M12 21.5V20M4 12H2.5M21.5 12H20M6.3 6.3 5.2 5.2M18.8 18.8l-1.1-1.1M17.7 6.3l1.1-1.1M5.2 18.8l1.1-1.1M12 16.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z',
  moon: 'M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z',
  menu: 'M4 7h16M4 12h16M4 17h16',
  edit: 'M4 20h4l10-10-4-4L4 16v4Zm10.5-13.5 4 4',
  logout: 'M15 12H4m0 0 3.5-3.5M4 12l3.5 3.5M11 4.5h6.5a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H11',
  shield: 'M12 3 5 5.5v5.2c0 4.3 2.9 8.2 7 9.8 4.1-1.6 7-5.5 7-9.8V5.5L12 3Zm-2.4 9 1.9 1.9 3.5-3.7',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 8.5c0-3.3 3.1-5.5 7-5.5s7 2.2 7 5.5',
  plus: 'M12 5v14M5 12h14',
  trash: 'M4 7h16M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7m2 0v12a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 7 19V7',
  save: 'M5 4h11l3 3v13H5V4Zm3 0v6h7V4M8 20v-5h8v5',
  eye: 'M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Zm9.5 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  crown: 'M4 17h16M4 17 2.5 7l5 3.5L12 5l4.5 5.5 5-3.5L20 17',
  back: 'M15 5l-7 7 7 7',
  bell: 'M18 9a6 6 0 1 0-12 0c0 5-2 6.5-2 6.5h16S18 14 18 9ZM10 19a2 2 0 0 0 4 0',
  inbox: 'M4 13h4l1.5 3h5L16 13h4M4 13l2.5-7h11L20 13v6H4v-6Z',
  check2: 'M4.5 12.5 9 17 19.5 6.5',
  close: 'M6 6l12 12M18 6 6 18',
  file: 'M6 4h7l5 5v11H6V4Zm7 0v5h5',
  refresh: 'M20 12a8 8 0 1 1-2.3-5.6M20 4v4h-4',
  login: 'M9 12h11m0 0-3.5-3.5M20 12l-3.5 3.5M11 4.5H5.5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2H11'
}
</script>

<template>
  <svg
    class="ico"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="PATHS[name] || ''" />
  </svg>
</template>
