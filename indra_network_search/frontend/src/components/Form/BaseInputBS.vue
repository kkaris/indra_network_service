<template>
  <div class="form-group">
    <label v-if="label">{{ label }}</label>
    <input
      v-bind="$attrs"
      :value="modelValue"
      :placeholder="ph"
      @input="$emit('update:modelValue', $event.target.value)"
      class="field form-control"
    >
  </div>
</template>

<script>
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
  computed: {
    ph() {
      return this.placeholder || this.label
    }
  }
}
</script>
