<template>
  <div class="card text-center">
    <div class="card-header">
      <div class="d-flex justify-content-between">
        <h2>
          Common Parents of <Node v-bind="source" /> and <Node v-bind="target" />
        </h2>
        <a
            role="button"
            data-bs-toggle="collapse"
            :href="`#${strUUID}`"
            :aria-expanded="false"
            :aria-controls="strUUID"
        >
          <i title="Click to expand" class="bi-plus-circle fs-2"></i>
        </a>
      </div>
    </div>
    <div class="card-body collapse show" id="assign UUID here">
      <div class="container">
        <template v-for="(pnode, key, index) in parents" :key="index">
          <div class="row">
            <div class="col">{{ pnode.name }}</div>
            <div class="col">{{ pnode.namespace }}</div>
            <div class="col">{{ pnode.identifier }}</div>
            <div class="col">
              <a :href="pnode.lookup"><i class="bi bi-box-arrow-up-right"></i></a>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import UniqueID from "@/helpers/BasicHelpers";
import Node from "@/components/Result/Node";

export default {
  components: {Node},
  props: {
    source: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isNode(obj)
      }
    },
    target: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isNode(obj)
      }
    },
    parents: {
      type: Array,
      required: true,
      validator: arr => {
        const isNotEmpty = arr.length > 0;
        const isNodeArray = sharedHelpers.isNodeArray(arr);

        return isNotEmpty && isNodeArray
      }
    }
  },
  setup() {
    const uuid = UniqueID().getID();
    return {
      uuid,
    }
  },
  computed: {
    strUUID() {
      return `collapse-${this.uuid}`
    },
  },
}
</script>
