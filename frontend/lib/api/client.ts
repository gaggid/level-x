import axios, { AxiosInstance, AxiosError } from "axios";
import { ApiResponse, User, AnalysisResult } from "@/types";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
      timeout: 60000, // 60 seconds for analysis
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - redirect to login
          this.clearToken();
          window.location.href = "/";
        }
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    return localStorage.getItem("auth_token");
  }

  private setToken(token: string): void {
    localStorage.setItem("auth_token", token);
  }

  private clearToken(): void {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
  }

  // Auth Methods
  async getAuthUrl(): Promise<ApiResponse<{ url: string }>> {
    try {
      const response = await this.client.get("/api/auth/url");
      return { success: true, data: response.data };
    } catch (error) {
      return this.handleError(error);
    }
  }

  async handleCallback(code: string, state: string): Promise<ApiResponse<User>> {
    try {
      const response = await this.client.post("/api/auth/callback", {
        code,
        state,
      });
      
      if (response.data.token) {
        this.setToken(response.data.token);
      }
      
      return { success: true, data: response.data.user };
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    try {
      const response = await this.client.get("/api/user/me");
      return { success: true, data: response.data };
    } catch (error) {
      return this.handleError(error);
    }
  }

  async logout(): Promise<void> {
    this.clearToken();
  }

  // Analysis Methods
  async runAnalysis(forceRefresh = false): Promise<ApiResponse<AnalysisResult>> {
    try {
      const response = await this.client.post("/api/analysis/run", {
        force_refresh_profile: forceRefresh,
        force_refresh_peers: forceRefresh,
      });
      return { success: true, data: response.data };
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getAnalysisHistory(): Promise<ApiResponse<AnalysisResult[]>> {
    try {
      const response = await this.client.get("/api/analysis/history");
      return { success: true, data: response.data };
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getAnalysisById(id: string): Promise<ApiResponse<AnalysisResult>> {
    try {
      const response = await this.client.get(`/api/analysis/${id}`);
      return { success: true, data: response.data };
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Error Handler
  private handleError(error: any): ApiResponse<never> {
    if (axios.isAxiosError(error)) {
      const message =
        error.response?.data?.message ||
        error.response?.data?.error ||
        error.message ||
        "An unexpected error occurred";
      
      return {
        success: false,
        error: message,
      };
    }
    
    return {
      success: false,
      error: "An unexpected error occurred",
    };
  }
}

// Export singleton instance
export const apiClient = new ApiClient();