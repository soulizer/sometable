import { FormViewModeType } from '@baserow/modules/database/formViewModeTypes'
import FormViewModeSurvey from '@baserow_premium/components/views/form/FormViewModeSurvey'
import FormViewModePreviewSurvey from '@baserow_premium/components/views/form/FormViewModePreviewSurvey'
import PremiumFeatures from '@baserow_premium/features'
import { FormSurveyModePaidFeature } from '@baserow_premium/paidFeatures'

export class FormViewSurveyModeType extends FormViewModeType {
  static getType() {
    return 'survey'
  }

  getName() {
    const { $i18n } = this.app
    return $i18n.t('formViewModeType.survey')
  }

  getDescription() {
    const { $i18n } = this.app
    return $i18n.t('formViewModeType.surveyDescription')
  }

  getIconClass() {
    return 'iconoir-reports'
  }

  getDeactivatedText() {
    const { $i18n } = this.app
    return $i18n.t('formViewModeType.onlyForPremium')
  }

  getDeactivatedClickModal() {
    return null
  }

  isDeactivated(workspaceId) {
    return false
  }

  getFormComponent() {
    return FormViewModeSurvey
  }

  getPreviewComponent() {
    return FormViewModePreviewSurvey
  }
}
