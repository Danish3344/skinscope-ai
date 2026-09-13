export const MAX_IMAGE_SIZE = 10 * 1024 * 1024
export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']

export function validateImageFile(file) {
  if (!file) return 'Choose an image to continue.'

  const extension = file.name.split('.').pop()?.toLowerCase()
  if (!ALLOWED_IMAGE_TYPES.includes(file.type) || !ALLOWED_IMAGE_EXTENSIONS.includes(extension)) {
    return 'Use a JPG, JPEG, PNG, or WEBP image.'
  }
  if (file.size === 0) return 'The selected image is empty.'
  if (file.size > MAX_IMAGE_SIZE) return 'The image must be 10 MB or smaller.'
  return null
}

export function readImageDimensions(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => {
      resolve({ width: image.naturalWidth, height: image.naturalHeight })
      URL.revokeObjectURL(url)
    }
    image.onerror = () => {
      reject(new Error('The selected file could not be decoded as an image.'))
      URL.revokeObjectURL(url)
    }
    image.src = url
  })
}

