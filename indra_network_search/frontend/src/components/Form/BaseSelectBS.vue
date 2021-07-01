<template>
  <div class="form-floating">
    <select
      class="form-select"
      :id="strUUID"
      :aria-label="`${label} select`"
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
    <label :for="strUUID" class="form-label" v-if="label">{{ label }}</label>
    <template v-if="errors.length > 0">
      <p
          v-for="error in errors"
          :key="error.$uid"
          style="color: #A00000">
        {{ error.$message ? error.$message : 'Invalid entry' }}
      </p>
    </template>
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
    options: {
      // Assumed to be an object with option.label and option.value
      type: Array,
      required: true
    },
    errors: {
      type: Array,
      default: () => {
        return [];
      }
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
      return `select${this.uuid}`
    }
  }
}
</script>
