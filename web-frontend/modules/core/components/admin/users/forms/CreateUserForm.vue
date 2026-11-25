<template>
  <form @submit.prevent="submit">
    <FormGroup
      small-label
      :label="$t('userForm.fullName')"
      required
      class="margin-bottom-2"
      :error="fieldHasErrors('name')"
    >
      <FormInput
        v-model="v$.values.name.$model"
        size="large"
        :error="fieldHasErrors('name')"
        @blur="v$.values.name.$touch"
      />
      <template #error>
        <span v-if="v$.values.name.required.$invalid">
          {{ $t('error.requiredField') }}
        </span>
        <span v-else-if="v$.values.name.minLength.$invalid">
          {{ $t('error.minLength', { min: 2 }) }}
        </span>
        <span v-else-if="v$.values.name.maxLength.$invalid">
          {{ $t('error.maxLength', { max: 60 }) }}
        </span>
        <span v-else-if="v$.values.name.nameIsNotEmail.$invalid">
          {{ $t('error.nameCantBeEmail') }}
        </span>
        <span v-else-if="v$.values.name.nameContainsNoUrl.$invalid">
          {{ $t('error.nameContainsUrl') }}
        </span>
        <span v-else-if="v$.values.name.nameContainsNoSpam.$invalid">
          {{ $t('error.nameContainsSpam') }}
        </span>
      </template>
    </FormGroup>

    <FormGroup
      small-label
      :label="$t('userForm.email')"
      required
      class="margin-bottom-2"
      :error="fieldHasErrors('username')"
    >
      <FormInput
        v-model="v$.values.username.$model"
        size="large"
        :error="fieldHasErrors('username')"
        @blur="v$.values.username.$touch"
      />
      <template #error>
        <span v-if="v$.values.username.required.$invalid">
          {{ $t('error.requiredField') }}
        </span>
        <span v-else-if="v$.values.username.email.$invalid">
          {{ $t('error.invalidEmail') }}
        </span>
      </template>
    </FormGroup>

    <FormGroup
      small-label
      :label="$t('changePasswordForm.newPassword')"
      required
      class="margin-bottom-2"
      :error="fieldHasErrors('password')"
    >
      <PasswordInput
        v-model="values.password"
        :validation-state="v$.values.password"
      />
    </FormGroup>

    <FormGroup
      small-label
      :label="$t('changePasswordForm.repeatPassword')"
      required
      class="margin-bottom-2"
      :error="fieldHasErrors('passwordConfirm')"
    >
      <FormInput
        v-model="values.passwordConfirm"
        type="password"
        size="large"
        :error="fieldHasErrors('passwordConfirm')"
        @blur="v$.values.passwordConfirm.$touch"
      />
      <template #error>
        {{ $t('changePasswordForm.error.doesntMatch') }}
      </template>
    </FormGroup>

    <FormGroup small-label :label="$t('userForm.isActive')">
      <Checkbox v-model="values.is_active" :disabled="loading" />
    </FormGroup>

    <FormGroup small-label :label="$t('user.isStaff')">
      <Checkbox v-model="values.is_staff" :disabled="loading" />
    </FormGroup>

    <FormGroup small-label :label="$t('usersAdminTable.emailVerified')">
      <Checkbox v-model="values.email_verified" :disabled="loading" />
    </FormGroup>

    <div class="actions">
      <div class="align-right">
        <Button
          type="primary"
          size="large"
          :disabled="loading || v$.$invalid"
          :loading="loading"
        >
          {{ $t('createUserModal.create') }}
        </Button>
      </div>
    </div>
  </form>
</template>

<script>
import { useVuelidate } from '@vuelidate/core'
import { reactive, computed } from 'vue'
import { email, maxLength, minLength, required, sameAs } from '@vuelidate/validators'
import PasswordInput from '@baserow/modules/core/components/helpers/PasswordInput'
import {
  nameContainsNoSpam,
  nameContainsNoUrl,
  nameIsNotEmail,
  passwordValidation,
} from '@baserow/modules/core/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'CreateUserForm',
  components: { PasswordInput },
  mixins: [form],
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
  },
  setup() {
    const values = reactive({
      values: {
        name: '',
        username: '',
        password: '',
        passwordConfirm: '',
        is_active: true,
        is_staff: false,
        email_verified: true,
      },
    })

    const rules = computed(() => ({
      values: {
        name: {
          required,
          minLength: minLength(2),
          maxLength: maxLength(60),
          nameIsNotEmail,
          nameContainsNoUrl,
          nameContainsNoSpam,
        },
        username: { required, email },
        password: passwordValidation,
        passwordConfirm: {
          sameAsPassword: sameAs(values.values.password),
        },
        is_active: {},
        is_staff: {},
        email_verified: {},
      },
    }))

    return {
      values: values.values,
      v$: useVuelidate(rules, values, { $lazy: true }),
    }
  },
  data() {
    return {
      allowedValues: [
        'name',
        'username',
        'password',
        'is_active',
        'is_staff',
        'email_verified',
      ],
    }
  },
}
</script>
