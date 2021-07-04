<template>
  <div class="form-floating">
    <input
      v-bind="$attrs"
      :id="strUUID"
      :value="modelValue"
      :placeholder="ph"
      :title="compTitle"
      @input="$emit('update:modelValue',
                    this.$attrs.disabled ? defaultValue :
                    $event.target.value)"
      class="form-control"
    >
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
    defaultValue: {
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
    errors: {
      type: Array,
      default: () => {
        return []
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
      return `input${this.uuid}`
    },
    ph() {
      return this.placeholder || this.label
    },
    compTitle() {
      return this.title || this.ph
    },
    isDisabled() {
      return document.getElementById(this.strUUID).disabled
    }
  }
}
</script>
