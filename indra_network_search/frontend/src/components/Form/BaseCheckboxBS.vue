<template>
  <div class="form-check">
    <input
        class="form-check-input"
        type="checkbox"
        v-bind="$attrs"
        :checked="modelValue"
        @change="$emit('update:modelValue', $event.target.checked)"
        :id="strUUID"
    />
    <label
        v-if="label"
        class="form-check-label"
        :for="strUUID"
    >{{ label }}</label>
  </div>
</template>

<script>
import UniqueID from "@/helpers/BasicHelpers";

export default {
  props: {
    label: {
      type: String,
      default: ''
    },
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  setup() {
    const uuid = UniqueID().getID();
    return {
      uuid
    }
  },
  computed: {
    strUUID() {
      return `checkbox${this.uuid}`
    }
  }
}
</script>
