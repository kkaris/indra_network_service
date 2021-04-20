<template>
  <div class="form-check">
    <input
      v-bind="$attrs"
      type="checkbox"
      :checked="modelValue"
      @change="$emit('update:modelValue', $event.target.checked)"
      class="field form-check-input"
    />
    <label
      v-if="label"
      class="form-check-label"
    >{{ label }}</label>
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
      type: Boolean,
      default: false
    }
  }
}
</script>
