export interface Profile {
  id: string;
  userId: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: 'M' | 'F' | 'O';
  nationality: string;
  address?: Address;
  phoneNumber?: string;
  avatarUrl?: string;
  licenseNumber?: string;
  licenseExpiryDate?: string;
  disciplines: Discipline[];
  medicalCertificate?: MedicalCertificate;
  club?: Club;
  achievements?: Achievement[];
}

export interface Address {
  street: string;
  city: string;
  postalCode: string;
  country: string;
}

export interface Discipline {
  id: string;
  name: string;
  grade?: Grade;
  startDate?: string;
  yearsOfExperience?: number;
}

export interface Grade {
  id: string;
  name: string;
  level: number;
  color: string;
  dateObtained: string;
  issuingAuthority: string;
}

export interface MedicalCertificate {
  id: string;
  issuanceDate: string;
  expiryDate: string;
  isValid: boolean;
  documentUrl?: string;
}

export interface Club {
  id: string;
  name: string;
  logoUrl?: string;
  address?: Address;
  role?: 'member' | 'coach' | 'admin';
  joinDate?: string;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  date: string;
  category: string;
  place?: number;
  competitionName?: string;
}