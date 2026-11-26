import { getModalTeleportedElement } from '@baserow/modules/core/utils/dom'

export default {
  mixins: [],
  provide() {
    return {
      registerChild: this.registerChild,
      unregisterChild: this.unregisterChild,
    }
  },
  inject: {
    parentRegisterModal: {
      from: 'registerChild',
      default: null,
    },
    parentUnregisterModal: {
      from: 'unregisterChild',
      default: null,
    },
  },
  emits: ['hidden', 'show'],
  data() {
    return {
      open: false,
      // Firefox and Chrome both can both have a different `target` element on `click`
      // when you release the mouse at different coordinates. Therefore we expect this
      // variable to be set on mousedown to be consistent.
      downElement: null,
      isModal: true,
      children: [],
      previousActiveElement: null,
    }
  },
  props: {
    canClose: {
      type: Boolean,
      default: true,
      required: false,
      mouseDownEvent: null,
    },
  },
  mounted() {
    this.$bus.$on('close-modals', this.hide)
    if (this.parentRegisterModal) {
      this.parentRegisterModal(this)
    }
  },
  beforeUnmount() {
    this.$bus.$off('close-modals', this.hide)
    window.removeEventListener('keyup', this.keyup)
    if (this.parentUnregisterModal) {
      this.parentUnregisterModal(this)
    }
  },
  methods: {
    /**
     * Toggle the open state of the modal.
     */
    toggle(value) {
      if (value === undefined) {
        value = !this.open
      }

      if (value) {
        this.show()
      } else {
        this.hide()
      }
    },
    /**
     * Returns if the modal is open or not.
     */
    isOpen() {
      return this.open
    },
    /**
     * Show the modal.
     */
    show() {
      this.previousActiveElement = document.activeElement
      this.open = true
      this.$emit('show')
      window.removeEventListener('keyup', this.keyup)
      window.addEventListener('keyup', this.keyup)
      document.removeEventListener('keydown', this.keydown, true)
      document.addEventListener('keydown', this.keydown, true)
      document.body.classList.add('prevent-scroll')
      const mouseDownEvent = (event) => {
        this.downElement = event.target
      }
      document.body.addEventListener('mousedown', mouseDownEvent)

      // store the handler for later removal
      this.mouseDownEvent = mouseDownEvent

      this.$nextTick(() => this.focusFirstElement())
    },
    /**
     * Hide the modal.
     */
    hide(emit = true) {
      if (!this.open) {
        return
      }

      const hasOpenChild = this.children.some((child) => child.open === true)

      // When the `esc` key is pressed and multiple modals are open, then we don't
      // want to close them all. Only last opened modal should close. This will make
      // sure that if there is an open child (modal or context), it will not hide
      // the parent modal.
      if (hasOpenChild) {
        return
      }

      // This is a temporary fix. What happens is the modal is opened by a context menu
      // item and the user closes the modal, the element is first deleted and then the
      // click outside event of the context is fired. It then checks if the click was
      // inside one of his children, but because the modal element doesn't exists
      // anymore it thinks it was outside, so is closes the context menu which we don't
      // want automatically.
      setTimeout(() => {
        this.open = false
      })

      // cleanup
      if (this.mouseDownEvent) {
        document.body.removeEventListener('mousedown', this.mouseDownEvent)
        this.mouseDownEvent = null
      }
      document.body.classList.remove('prevent-scroll')
      window.removeEventListener('keyup', this.keyup)
      document.removeEventListener('keydown', this.keydown, true)

      if (emit) {
        this.$emit('hidden')
      }

      this.$nextTick(() => {
        const previous = this.previousActiveElement
        this.previousActiveElement = null
        if (previous && typeof previous.focus === 'function') {
          previous.focus()
        }
      })
    },
    getFocusableElements() {
      const root = this.$refs.modalEl
      if (!root) {
        return []
      }
      return [
        ...root.querySelectorAll(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        ),
      ].filter(
        (element) =>
          element.getClientRects().length > 0 &&
          getComputedStyle(element).visibility !== 'hidden'
      )
    },
    focusFirstElement() {
      if (!this.open || this.children.some((child) => child.open === true)) {
        return
      }
      const root = this.$refs.modalEl
      if (root && root.contains(document.activeElement)) {
        return
      }
      const focusable = this.getFocusableElements()
      if (focusable.length > 0) {
        focusable[0].focus()
      } else {
        root?.querySelector('.modal__box')?.focus()
      }
    },
    keydown(event) {
      if (!this.open || event.key !== 'Tab') {
        return
      }
      if (this.children.some((child) => child.open === true)) {
        return
      }
      const focusable = this.getFocusableElements()
      if (focusable.length === 0) {
        event.preventDefault()
        return
      }
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    },
    registerChild(child) {
      this.children.push(child)
    },
    unregisterChild(child) {
      const index = this.children.indexOf(child)
      if (index !== -1) {
        this.children.splice(index, 1)
      }
    },
    /**
     * If someone actually clicked on the modal wrapper and not one of his children the
     * modal should be closed.
     */
    outside() {
      if (this.downElement === this.$refs.modalEl && this.canClose) {
        this.hide()
      }
    },
    /**
     * When the escape key is pressed the modal needs to be hidden.
     */
    keyup(event) {
      if (event.key === 'Escape' && this.canClose) {
        this.hide()
      }
    },
    getTeleportedElement() {
      return getModalTeleportedElement(this.$refs)
    },
  },
}
