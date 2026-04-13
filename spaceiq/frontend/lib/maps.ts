export function mapEmbedUrl(latitude?: number | null, longitude?: number | null) {
  if (!latitude || !longitude) {
    return "https://maps.google.com?output=embed";
  }
  return `https://www.google.com/maps?q=${latitude},${longitude}&z=15&output=embed`;
}
