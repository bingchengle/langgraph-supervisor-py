<template>
  <!-- 专属标志：侧视游鱼轮廓 + 镂空「YU」字母负形，一体成型 -->
  <svg
    class="yu-fish-logo"
    viewBox="0 0 320 120"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <defs>
      <linearGradient id="yuFishSkin" x1="0%" y1="15%" x2="100%" y2="85%">
        <stop offset="0%" stop-color="#fef9c3" />
        <stop offset="30%" stop-color="#c7d2fe" />
        <stop offset="65%" stop-color="#6366f1" />
        <stop offset="100%" stop-color="#312e81" />
      </linearGradient>
      <linearGradient id="yuFishBelly" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="rgba(255,255,255,0.45)" />
        <stop offset="100%" stop-color="rgba(255,255,255,0)" />
      </linearGradient>
      <mask id="yuFishMask" maskUnits="userSpaceOnUse" x="0" y="0" width="320" height="120">
        <rect width="320" height="120" fill="black" />
        <!-- 鱼形外轮廓（白=显示） -->
        <path fill="white" :d="fishPath" />
        <!-- 黑字=镂空，透出封面背景 -->
        <text
          x="168"
          y="80"
          text-anchor="middle"
          fill="black"
          transform="rotate(-3.5 168 80)"
          class="yu-monogram"
        >
          YU
        </text>
      </mask>
    </defs>

    <g class="yu-fish-group">
      <rect width="320" height="120" fill="url(#yuFishSkin)" mask="url(#yuFishMask)" />
      <path :d="bellyPath" fill="url(#yuFishBelly)" mask="url(#yuFishMask)" opacity="0.9" />
      <circle class="yu-fish-eye" cx="250" cy="46" r="5" />
      <circle class="yu-fish-eye-glint" cx="251.2" cy="44.8" r="1.6" />
    </g>
  </svg>
</template>

<script setup>
/**
 * 单路径鱼形：左侧尾鳍分叉呈「人」字游姿，右侧圆头；与镂空 YU 共同构成品牌图形。
 */
const fishPath =
  'M 18 58 ' +
  'C 10 32 28 8 52 26 ' +
  'C 62 32 66 44 68 52 ' +
  'C 42 64 28 82 22 94 ' +
  'C 16 102 6 88 12 68 ' +
  'C 14 62 18 58 18 58 ' +
  'Z ' +
  'M 68 52 ' +
  'C 130 28 210 14 262 34 ' +
  'C 308 48 314 82 288 98 ' +
  'C 248 118 120 108 76 84 ' +
  'C 68 74 64 60 68 52 ' +
  'Z'

const bellyPath =
  'M 78 76 ' +
  'C 150 96 230 100 276 82 ' +
  'C 232 108 140 112 86 92 ' +
  'C 80 86 78 80 78 76 ' +
  'Z'
</script>

<style scoped>
.yu-fish-logo {
  width: 280px;
  height: 105px;
  max-width: min(280px, 88vw);
  display: block;
  margin: 0 auto;
  filter: drop-shadow(0 6px 24px rgba(15, 23, 42, 0.55));
}

.yu-monogram {
  font-family: Georgia, 'Times New Roman', 'Noto Serif SC', serif;
  font-size: 50px;
  font-weight: 700;
  font-style: italic;
  letter-spacing: -0.05em;
}

.yu-fish-group {
  transform: translateY(1px);
}

.yu-fish-eye {
  fill: #0f172a;
}

.yu-fish-eye-glint {
  fill: #f8fafc;
  opacity: 0.92;
}
</style>
