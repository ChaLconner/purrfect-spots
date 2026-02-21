<template>
  <div class="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-background">
    <!-- Blobs -->
    <div
      class="absolute top-0 -left-4 w-96 h-96 bg-primary/30 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob"
    ></div>
    <div
      class="absolute top-0 -right-4 w-96 h-96 bg-secondary/30 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob [animation-delay:2s]"
    ></div>
    <div
      class="absolute -bottom-8 left-20 w-96 h-96 bg-accent/30 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob [animation-delay:4s]"
    ></div>

    <!-- Extra blobs for fullness -->
    <div
      class="absolute bottom-1/4 right-1/4 w-64 h-64 bg-primary/20 rounded-full mix-blend-multiply filter blur-3xl opacity-60 animate-blob [animation-delay:1s]"
    ></div>
  </div>
</template>
