import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { mockLeaveTypes } from '../data/mockData'

const SubmitLeaveRequest = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    leaveType: '',
    startDate: '',
    endDate: '',
    reason: '',
    emergencyContact: '',
    emergencyPhone: ''
  })
  const [errors, setErrors] = useState({})
  const [isLoading, setIsLoading] = useState(false)

  const leaveTypes = mockLeaveTypes

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  const calculateDays = () => {
    if (!formData.startDate || !formData.endDate) return 0
    
    const start = new Date(formData.startDate)
    const end = new Date(formData.endDate)
    const diffTime = Math.abs(end - start)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays + 1 // Include both start and end dates
  }

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.leaveType) {
      newErrors.leaveType = 'Please select a leave type'
    }
    
    if (!formData.startDate) {
      newErrors.startDate = 'Start date is required'
    } else {
      const startDate = new Date(formData.startDate)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      if (startDate < today) {
        newErrors.startDate = 'Start date cannot be in the past'
      }
    }
    
    if (!formData.endDate) {
      newErrors.endDate = 'End date is required'
    } else if (formData.startDate && formData.endDate) {
      const startDate = new Date(formData.startDate)
      const endDate = new Date(formData.endDate)
      if (endDate < startDate) {
        newErrors.endDate = 'End date cannot be before start date'
      }
    }
    
    if (!formData.reason) {
      newErrors.reason = 'Please provide a reason for your leave request'
    } else if (formData.reason.length < 10) {
      newErrors.reason = 'Reason must be at least 10 characters long'
    }
    
    if (formData.leaveType === 'sick' || formData.leaveType === 'personal') {
      if (!formData.emergencyContact) {
        newErrors.emergencyContact = 'Emergency contact is required for this leave type'
      }
      if (!formData.emergencyPhone) {
        newErrors.emergencyPhone = 'Emergency phone number is required for this leave type'
      }
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) return
    
    setIsLoading(true)
    
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Simulate successful submission
      alert('Leave request submitted successfully! You will receive a confirmation email shortly.')
      navigate('/my-leaves')
    } catch (error) {
      console.error('Submission error:', error)
      setErrors({ general: 'Failed to submit leave request. Please try again.' })
    } finally {
      setIsLoading(false)
    }
  }

  const days = calculateDays()

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Submit Leave Request</h1>
            <p className="mt-2 text-sm text-gray-600">
              Fill out the form below to request time off. All requests are subject to approval.
            </p>
          </div>

          {errors.general && (
            <div className="mb-6 rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{errors.general}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Leave Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Leave Type <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {leaveTypes.map((type) => (
                  <label
                    key={type.value}
                    className={`relative flex cursor-pointer rounded-lg border p-4 shadow-sm focus:outline-none ${
                      formData.leaveType === type.value
                        ? 'border-indigo-500 ring-2 ring-indigo-500'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <input
                      type="radio"
                      name="leaveType"
                      value={type.value}
                      checked={formData.leaveType === type.value}
                      onChange={handleChange}
                      className="sr-only"
                    />
                    <div className="flex flex-1">
                      <div className="flex flex-col">
                        <span className="block text-sm font-medium text-gray-900">{type.label}</span>
                        <span className="mt-1 flex items-center text-sm text-gray-500">{type.description}</span>
                      </div>
                    </div>
                    <div className={`ml-3 flex h-5 w-5 items-center justify-center ${
                      formData.leaveType === type.value ? 'text-indigo-600' : 'text-gray-300'
                    }`}>
                      {formData.leaveType === type.value && (
                        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 12 12">
                          <path d="M9.707 3.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L5 6.586l3.293-3.293a1 1 0 011.414 0z" />
                        </svg>
                      )}
                    </div>
                  </label>
                ))}
              </div>
              {errors.leaveType && (
                <p className="mt-2 text-sm text-red-600">{errors.leaveType}</p>
              )}
            </div>

            {/* Date Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">
                  Start Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  id="startDate"
                  name="startDate"
                  value={formData.startDate}
                  onChange={handleChange}
                  className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                    errors.startDate ? 'border-red-300' : ''
                  }`}
                />
                {errors.startDate && (
                  <p className="mt-2 text-sm text-red-600">{errors.startDate}</p>
                )}
              </div>

              <div>
                <label htmlFor="endDate" className="block text-sm font-medium text-gray-700">
                  End Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  id="endDate"
                  name="endDate"
                  value={formData.endDate}
                  onChange={handleChange}
                  className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                    errors.endDate ? 'border-red-300' : ''
                  }`}
                />
                {errors.endDate && (
                  <p className="mt-2 text-sm text-red-600">{errors.endDate}</p>
                )}
              </div>
            </div>

            {/* Days Calculation */}
            {days > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">
                      Leave Duration: {days} day{days !== 1 ? 's' : ''}
                    </h3>
                    <div className="mt-2 text-sm text-blue-700">
                      <p>This request covers {days} working day{days !== 1 ? 's' : ''}.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Reason */}
            <div>
              <label htmlFor="reason" className="block text-sm font-medium text-gray-700">
                Reason for Leave <span className="text-red-500">*</span>
              </label>
              <textarea
                id="reason"
                name="reason"
                rows={4}
                value={formData.reason}
                onChange={handleChange}
                placeholder="Please provide a detailed reason for your leave request..."
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                  errors.reason ? 'border-red-300' : ''
                }`}
              />
              {errors.reason && (
                <p className="mt-2 text-sm text-red-600">{errors.reason}</p>
              )}
              <p className="mt-2 text-sm text-gray-500">
                Please provide sufficient detail to help with the approval process.
              </p>
            </div>

            {/* Emergency Contact (for certain leave types) */}
            {(formData.leaveType === 'sick' || formData.leaveType === 'personal') && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-yellow-800">Emergency Contact Information</h3>
                  <p className="mt-1 text-sm text-yellow-700">
                    Please provide emergency contact details for this leave request.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="emergencyContact" className="block text-sm font-medium text-gray-700">
                      Emergency Contact Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      id="emergencyContact"
                      name="emergencyContact"
                      value={formData.emergencyContact}
                      onChange={handleChange}
                      placeholder="Full name of emergency contact"
                      className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                        errors.emergencyContact ? 'border-red-300' : ''
                      }`}
                    />
                    {errors.emergencyContact && (
                      <p className="mt-2 text-sm text-red-600">{errors.emergencyContact}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="emergencyPhone" className="block text-sm font-medium text-gray-700">
                      Emergency Phone Number <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="tel"
                      id="emergencyPhone"
                      name="emergencyPhone"
                      value={formData.emergencyPhone}
                      onChange={handleChange}
                      placeholder="Phone number with country code"
                      className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                        errors.emergencyPhone ? 'border-red-300' : ''
                      }`}
                    />
                    {errors.emergencyPhone && (
                      <p className="mt-2 text-sm text-red-600">{errors.emergencyPhone}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate('/')}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Submitting...
                  </>
                ) : (
                  'Submit Leave Request'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default SubmitLeaveRequest
