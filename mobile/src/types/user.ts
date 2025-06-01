export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  permissions: string[];
  organization?: {
    id: string;
    name: string;
    type: string;
  };
}

export type UserRole = 
  | 'admin' 
  | 'federation_admin'
  | 'club_admin'
  | 'coach'
  | 'referee'
  | 'practitioner';