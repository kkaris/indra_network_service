<template>
  <div class="form-group">
    <label v-if="label">{{ label }}</label>
    <select
      class="field form-control"
      :value="modelValue"
      v-bind="{
        ...$attrs,
        onChange: ($event) => { $emit('update:modelValue', $event.target.value) }
      }"
    >
      <option
        v-for="option in options"
        :value="option.value"
        :key="option.value"
        :selected="option.value === modelValue"
      >{{ option.label }}</option>
    </select>
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
    options: {
      // Assumed to be an object with option.label and option.value
      type: Array,
      required: true
    }
  }
}
</script>
