<template>
  <div class="form-floating">
    <input
      v-bind="$attrs"
      :id="strUUID"
      :value="modelValue"
      :placeholder="ph"
      :title="compTitle"
      @input="$emit('update:modelValue', $event.target.value)"
      class="form-control"
    >
    <label :for="strUUID" class="form-label" v-if="label">{{ label }}</label>
    <p v-if="error" style="color: #A00000">{{ error }}</p>
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
    },
    title: {
      type: String,
      default: ''
    },
    error: {
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
    },
    compTitle() {
      return this.title || this.ph
    }
  }
}
</script>
