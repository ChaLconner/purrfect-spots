import { onMounted, onUnmounted, watch, type Ref, isRef } from 'vue';

type SchemaData = Record<string, unknown>;

export function useStructuredData(data: SchemaData | Ref<SchemaData>): void {
  let scriptElement: HTMLScriptElement | null = null;

  const updateSchema = (schemaData: SchemaData): void => {
    if (!scriptElement) {
      scriptElement = document.createElement('script');
      scriptElement.setAttribute('type', 'application/ld+json');
      document.head.appendChild(scriptElement);
    }
    scriptElement.textContent = JSON.stringify(schemaData);
  };

  onMounted(() => {
    const initialData = isRef(data) ? data.value : data;
    updateSchema(initialData);

    if (isRef(data)) {
      watch(data, (newData) => {
        updateSchema(newData);
      });
    }
  });

  onUnmounted(() => {
    if (scriptElement && document.head.contains(scriptElement)) {
      document.head.removeChild(scriptElement);
    }
  });
}
