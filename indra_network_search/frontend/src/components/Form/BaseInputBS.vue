<template>
  <div class="form-floating">
    <input
      v-bind="$attrs"
      :id="strUUID"
      :value="modelValue"
      :placeholder="ph"
      :title="ph"
      @input="$emit('update:modelValue', $event.target.value)"
      class="form-control"
    >
    <label :for="strUUID" class="form-label" v-if="label">{{ label }}</label>
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
      type: [String, Number],
      default: ''
    },
    placeholder: {
      type: String,
      default: ''
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
      return `input${this.uuid}`
    },
    ph() {
      return this.placeholder || this.label
    }
  }
}
</script>
