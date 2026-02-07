<template>
  <div class="min-h-screen bg-sand-50 py-12 px-4 sm:px-6 lg:px-8">
    <div
      class="max-w-4xl mx-auto bg-white rounded-2xl shadow-sm border border-sand-100 p-8 sm:p-12"
    >
      <h1 class="text-3xl font-bold text-brown-900 font-display mb-8">Privacy Policy</h1>

      <div class="prose prose-brown max-w-none text-brown-700">
        <p class="text-sm text-brown-500 mb-6">
          Last Updated: {{ new Date().toLocaleDateString() }}
        </p>

        <p>
          At Purrfect Spots ("we", "us", or "our"), we respect your privacy and are committed to
          protecting your personal data. This Privacy Policy explains how we collect, use, and
          safeguard your information when you visit our website
          <a href="https://purrfectspots.xyz" class="text-terracotta-600 hover:text-terracotta-700"
            >purrfectspots.xyz</a
          >.
        </p>

        <h3>1. Information We Collect</h3>
        <p>
          We collect information that you voluntarily provide to us when you register on the
          website, use our services, or contact us.
        </p>
        <ul>
          <li>
            <strong>Personal Data:</strong> Name, email address, and profile picture (via Google
            Login or manual registration).
          </li>
          <li>
            <strong>Content Data:</strong> Photos, comments, likes, and location data you upload to
            the platform.
          </li>
          <li>
            <strong>Usage Data:</strong> Information about how you interact with our website (e.g.,
            pages visited, time spent).
          </li>
        </ul>

        <h3>2. How We Use Your Information</h3>
        <p>We use the collected information for the following purposes:</p>
        <ul>
          <li>To provide and maintain our Service.</li>
          <li>To notify you about changes to our Service.</li>
          <li>
            To allow you to participate in interactive features (e.g., uploading photos,
            commenting).
          </li>
          <li>To provide customer support.</li>
          <li>To detect, prevent, and address technical issues.</li>
        </ul>

        <h3>3. Data Sharing and Disclosure</h3>
        <p>
          We do not sell your personal data. We may share your information with third-party service
          providers (e.g., Google Cloud, Supabase, Stripe) solely for the purpose of operating our
          Service. These providers are obligated to protect your data.
        </p>

        <h3>4. Cookies and Tracking Technologies</h3>
        <p>
          We use cookies and similar tracking technologies to track the activity on our Service and
          hold certain information. You can instruct your browser to refuse all cookies or to
          indicate when a cookie is being sent.
        </p>

        <h3>5. User Rights</h3>
        <p>
          Depending on your location, you may have the following rights regarding your personal
          data:
        </p>
        <ul>
          <li>The right to access, update, or delete the information we have on you.</li>
          <li>The right of rectification.</li>
          <li>The right to object.</li>
          <li>The right of restriction.</li>
        </ul>
        <p>To exercise these rights, please contact us at support@purrfectspots.com.</p>

        <h3>6. Changes to This Privacy Policy</h3>
        <p>
          We may update our Privacy Policy from time to time. We will notify you of any changes by
          posting the new Privacy Policy on this page.
        </p>

        <h3>7. Contact Us</h3>
        <p>
          If you have any questions about this Privacy Policy, please contact us by email:
          support@purrfectspots.com.
        </p>
      </div>

      <div class="mt-8 pt-8 border-t border-sand-200">
        <router-link to="/" class="text-terracotta-600 hover:text-terracotta-700 font-medium">
          &larr; Back to Home
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Static content, no script logic needed
</script>
