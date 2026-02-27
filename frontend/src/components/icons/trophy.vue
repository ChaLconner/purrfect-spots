<template>
  <svg
    viewBox="0 0 24 24"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
  >
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M15.5 3.5H5.5C4.39543 3.5 3.5 4.39543 3.5 5.5V7.5C3.5 8.60457 4.39543 9.5 5.5 9.5H6.67071C7.1974 12.3561 9.1896 14.643 12 15.3286V18.5H10C9.4477 18.5 9 18.9477 9 19.5C9 20.0523 9.4477 20.5 10 20.5H14C14.5523 20.5 15 20.0523 15 19.5C15 18.9477 14.5523 18.5 14 18.5H12V15.3286C14.8104 14.643 16.8026 12.3561 17.3293 9.5H18.5C19.6046 9.5 20.5 8.60457 20.5 7.5V5.5C20.5 4.39543 19.6046 3.5 18.5 3.5H15.5ZM5.5 7.5V5.5H6.67071V7.5H5.5ZM18.5 7.5H17.3293V5.5H18.5V7.5Z"
    />
  </svg>
</template>

<script setup>
defineProps({
  size: {
    type: [String, Number],
    default: '100%',
  },
});
</script>
