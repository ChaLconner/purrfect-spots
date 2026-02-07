<template>
  <svg
    viewBox="0 0 24 24"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
  >
    <path
      d="M17 3H7C5.89543 3 5 3.89543 5 5V7C5 8.10457 5.89543 9 7 9H8.17071C8.6974 11.8561 10.6896 14.143 13.5 14.8286V18H11C10.4477 18 10 18.4477 10 19C10 19.5523 10.4477 20 11 20H15C15.5523 20 16 19.5523 16 19C16 18.4477 15.5523 18 15 18H13.5V14.8286C16.3104 14.143 18.3026 11.8561 18.8293 9H20C21.1046 9 22 8.10457 22 7V5C22 3.89543 21.1046 3 20 3H17ZM7 7V5H8.17071V7H7ZM20 7H18.8293V5H20V7Z"
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
