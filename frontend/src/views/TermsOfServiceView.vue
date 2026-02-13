<template>
  <div class="min-h-screen bg-sand-50 py-12 px-4 sm:px-6 lg:px-8">
    <div
      class="max-w-4xl mx-auto bg-white rounded-2xl shadow-sm border border-sand-100 p-8 sm:p-12"
    >
      <h1 class="text-3xl font-bold text-brown-900 font-display mb-8">Terms of Service</h1>

      <div class="prose prose-brown max-w-none text-brown-700">
        <p class="text-sm text-brown-500 mb-6">
          Last Updated: {{ new Date().toLocaleDateString() }}
        </p>

        <p>
          Welcome to Purrfect Spots ("Services"). By using our website
          <a
            href="https://purrfectspots.xyz"
            class="text-terracotta-600 hover:text-terracotta-700"
          >purrfectspots.xyz</a>, you agree to be bound by these Terms of Service. If you disagree with any part of the
          terms, you must not use our Services.
        </p>

        <h3>1. Acceptance of Terms</h3>
        <p>
          By accessing or using the Service, you agree to be bound by these Terms. If you disagree
          with any part of the terms, then you may not access the Service.
        </p>

        <h3>2. Description of Service</h3>
        <p>
          Purrfect Spots is a platform for users to upload, share, and discover photos and locations
          of cats. We reserve the right to modify or discontinue the Service at any time without
          notice.
        </p>

        <h3>3. User Accounts</h3>
        <p>
          When you create an account with us, you must provide accurate and complete information.
          You are solely responsible for safeguard ing your account password and for all activities
          that occur under your account. You must notify us immediately of any unauthorized use of
          your account.
        </p>

        <h3>4. User Content and Conduct</h3>
        <p>
          You retain ownership of the content you upload ("User Content"), but you grant us a
          worldwide, royalty-free license to use, reproduce, modify, adapt, publish, and display
          such content.
        </p>
        <p><strong>You agree NOT to upload content that:</strong></p>
        <ul>
          <li>
            Is illegal, harmful, threatening, abusive, harassing, defamatory, vulgar, obscene, or
            invasive of another's privacy.
          </li>
          <li>
            Infringes on any patent, trademark, trade secret, copyright, or other proprietary rights
            of any party.
          </li>
          <li>
            Contains software viruses or any other computer code designed to interrupt, destroy, or
            limit the functionality of any computer software or hardware.
          </li>
          <li>Promotes hate speech, violence, or discrimination.</li>
          <li>Is sexually explicit or pornographic.</li>
        </ul>
        <p>
          We reserve the right to remove any content that violates these Terms or is otherwise
          objectionable, at our sole discretion.
        </p>

        <h3>5. Intellectual Property</h3>
        <p>
          The Service and its original content (excluding User Content), features, and functionality
          are and will remain the exclusive property of Purrfect Spots and its licensors.
        </p>

        <h3>6. Termination</h3>
        <p>
          We may terminate or suspend your account immediately, without prior notice or liability,
          for any reason whatsoever, including without limitation if you breach the Terms.
        </p>

        <h3>7. Limitation of Liability</h3>
        <p>
          In no event shall Purrfect Spots, nor its directors, employees, partners, agents,
          suppliers, or affiliates, be liable for any indirect, incidental, special, consequential
          or punitive damages, including without limitation, loss of profits, data, use, goodwill,
          or other intangible losses, resulting from (i) your access to or use of or inability to
          access or use the Service; (ii) any conduct or content of any third party on the Service;
          (iii) any content obtained from the Service; and (iv) unauthorized access, use or
          alteration of your transmissions or content, whether based on warranty, contract, tort
          (including negligence) or any other legal theory, whether or not we have been informed of
          the possibility of such damage.
        </p>

        <h3>8. Disclaimer</h3>
        <p>
          Your use of the Service is at your sole risk. The Service is provided on an "AS IS" and
          "AS AVAILABLE" basis. The Service is provided without warranties of any kind, whether
          express or implied.
        </p>

        <h3>9. Governing Law</h3>
        <p>
          These Terms shall be governed and construed in accordance with the laws of Thailand,
          without regard to its conflict of law provisions.
        </p>

        <h3>10. Changes</h3>
        <p>
          We reserve the right, at our sole discretion, to modify or replace these Terms at any
          time. By continuing to access or use our Service after those revisions become effective,
          you agree to be bound by the revised terms.
        </p>

        <h3>11. Contact Us</h3>
        <p>
          If you have any questions about these Terms, please contact us by email:
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
// Static content
</script>
